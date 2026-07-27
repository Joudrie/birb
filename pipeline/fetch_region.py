#!/usr/bin/env python3
"""Build a region's bird dataset from GBIF.

Reads the eBird Observation Dataset through GBIF (no API key, openly licensed),
and derives the two numbers the app is built on:

  reportingIndex  a species' record count as a fraction of the region's
                  most-reported bird. A relative index, NOT "% of checklists" --
                  GBIF gives no count of distinct checklists, so there is no
                  denominator for a true percentage.

  seasonality     monthly counts divided by the region's own monthly record
                  volume, rescaled so the species' best month is 1.0. Raw counts
                  describe birders, not birds: Massachusetts birding puts 20.7%
                  of the year's records in May and 5.2% in February, so without
                  this correction nearly every species looks like a spring
                  migrant.

Usage:
    python3 fetch_region.py --gadm USA.22_1 --slug us-ma --name Massachusetts --top 420
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

API = "https://api.gbif.org/v1"

# The eBird Observation Dataset. Roughly 98% of the bird records GBIF returns
# for a US state come from here anyway; pinning it makes that explicit.
EBIRD_DATASET_KEY = "4fa7b334-ce0d-4e88-aaae-2e0c138d049e"

USER_AGENT = "birdwatch-pipeline/1.0 (+https://github.com/seanjoudrie/birb)"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_DIR = os.path.join(ROOT, "data")
NAME_OVERRIDES = os.path.join(HERE, "name_overrides.json")

# reportingIndex thresholds. The vagrant floor is a design decision, not a
# statistical one: below it the tail stops being rare birds and becomes
# one-record strays and escaped captives. They stay in the dataset -- finding
# one should be a delight -- but they are never dealt into a deck.
TIERS = [
    ("common", 0.25),
    ("uncommon", 0.06),
    ("rare", 0.015),
    ("super_rare", 0.002),
    ("vagrant", 0.0),
]
DECK_INELIGIBLE = {"vagrant"}

# Birds that certainly occur in the region. When GBIF's backbone drops a species
# -- as it does for Cooper's Hawk, whose genus Astur is marked DOUBTFUL -- the
# output does not look wrong, the species is simply absent. Extend this for
# every new region.
EXPECT = {
    "USA.22_1": [  # Massachusetts
        "Cyanocitta cristata",        # Blue Jay
        "Poecile atricapillus",       # Black-capped Chickadee
        "Turdus migratorius",         # American Robin
        "Cardinalis cardinalis",      # Northern Cardinal
        "Branta canadensis",          # Canada Goose
        "Larus smithsonianus",        # Herring Gull (GBIF splits it from L. argentatus)
        "Buteo jamaicensis",          # Red-tailed Hawk
        "Dryobates pubescens",        # Downy Woodpecker
        "Sialia sialis",              # Eastern Bluebird
        "Archilochus colubris",       # Ruby-throated Hummingbird
        "Haliaeetus leucocephalus",   # Bald Eagle
        "Meleagris gallopavo",        # Wild Turkey
    ],
}

MONTHS = list(range(1, 13))


def get(path, params=None, tries=5):
    """GET JSON from GBIF, retrying on transient failures."""
    url = f"{API}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    delay = 1.0
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            if attempt == tries - 1:
                raise RuntimeError(f"GBIF request failed after {tries} tries: {url}") from exc
            time.sleep(delay)
            delay *= 2
    raise AssertionError("unreachable")


def occurrence_search(gadm, years, **extra):
    params = {
        "datasetKey": EBIRD_DATASET_KEY,
        "gadmGid": gadm,
        "year": f"{years[0]},{years[1]}",
        "limit": 0,
    }
    params.update(extra)
    return get("occurrence/search", params)


def facet_counts(payload, field):
    for facet in payload.get("facets", []):
        if facet["field"] == field:
            return {c["name"]: c["count"] for c in facet["counts"]}
    return {}


def monthly_vector(counts):
    """Facet dict keyed by month-as-string -> a 12-slot list."""
    return [counts.get(str(m), 0) for m in MONTHS]


def classify_season(curve):
    """Label an effort-corrected, max-normalised 12-month curve.

    Order matters. A passage migrant is low in both June and December, so on a
    plain summer-vs-winter comparison it would fall out as whichever of the two
    it happens to be marginally less absent in. Check the double peak first.
    """
    def window(months):
        return sum(curve[m - 1] for m in months) / len(months)

    winter = window([12, 1, 2])
    spring = window([3, 4, 5])
    summer = window([6, 7, 8])
    fall = window([9, 10, 11])

    strong = sum(1 for v in curve if v >= 0.40)

    # Present all year at real strength.
    if min(curve) >= 0.30 or strong >= 10:
        return "year_round"

    # Two shoulder peaks with a gap in both June and December: passing through.
    passage = (spring + fall) / 2
    resident = max(summer, winter)
    if passage > 1.35 * resident and summer < 0.65 and winter < 0.65:
        return "migrant"

    if summer > winter:
        return "summer" if winter < 0.40 else "year_round"
    return "winter" if summer < 0.40 else "year_round"


def tier_for(index):
    for name, floor in TIERS:
        if index >= floor:
            return name
    return TIERS[-1][0]


def load_overrides():
    if not os.path.exists(NAME_OVERRIDES):
        return {}
    with open(NAME_OVERRIDES, encoding="utf-8") as fh:
        return {k: v for k, v in json.load(fh).items() if not k.startswith("_")}


def species_record(key, gadm, years, records):
    """Fetch one species' taxonomy and effort-corrected monthly curve."""
    taxon = get(f"species/{key}")
    payload = occurrence_search(gadm, years, speciesKey=key, facet="month", facetLimit=12)
    return {
        "speciesKey": key,
        "records": records,
        "scientificName": taxon.get("canonicalName") or taxon.get("scientificName"),
        "authorship": taxon.get("scientificName"),
        "commonName": taxon.get("vernacularName"),
        "family": taxon.get("family"),
        "order": taxon.get("order"),
        "class": taxon.get("class"),
        "monthlyRecords": monthly_vector(facet_counts(payload, "MONTH")),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gadm", required=True, help="GADM region id, e.g. USA.22_1")
    ap.add_argument("--slug", required=True, help="output slug, e.g. us-ma")
    ap.add_argument("--name", required=True, help="human region name, e.g. Massachusetts")
    ap.add_argument("--top", type=int, default=420, help="how many species to keep")
    ap.add_argument("--years", default="2015,2026", help="inclusive year range")
    ap.add_argument("--workers", type=int, default=8, help="parallel GBIF requests")
    ap.add_argument("--out", default=None, help="output path (default data/<slug>.json)")
    args = ap.parse_args()

    years = tuple(int(y) for y in args.years.split(","))
    started = time.time()

    # 1. Region effort. Every seasonality curve is measured against this.
    print(f"region {args.name} ({args.gadm}) {years[0]}-{years[1]}")
    region = occurrence_search(args.gadm, years, facet="month", facetLimit=12)
    total_records = region["count"]
    effort = monthly_vector(facet_counts(region, "MONTH"))
    if total_records == 0 or min(effort) == 0:
        sys.exit(f"error: no records for {args.gadm}; check the GADM id")
    peak_effort_month = effort.index(max(effort)) + 1
    low_effort_month = effort.index(min(effort)) + 1
    print(f"  {total_records:,} records; "
          f"effort peaks month {peak_effort_month} "
          f"({max(effort) / total_records:.1%}), "
          f"bottoms month {low_effort_month} "
          f"({min(effort) / total_records:.1%}) "
          f"-- a {max(effort) / min(effort):.1f}x swing")

    # 2. The region's species, by record count.
    faceted = occurrence_search(args.gadm, years, facet="speciesKey", facetLimit=args.top)
    ranked = sorted(((int(key), count) for key, count
                     in facet_counts(faceted, "SPECIES_KEY").items()),
                    key=lambda kv: -kv[1])
    print(f"  {len(ranked)} species keys")

    # 3. Per-species taxonomy and monthly counts.
    print(f"fetching species detail ({args.workers} workers)")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        raw = list(pool.map(
            lambda item: species_record(item[0], args.gadm, years, item[1]), ranked))

    overrides = load_overrides()
    top_count = max(r["records"] for r in raw)
    species = []
    warnings = []

    for rec in raw:
        if rec.get("class") != "Aves":
            warnings.append(f"skipped non-bird taxon {rec['scientificName']} "
                            f"(class {rec.get('class')})")
            continue

        sci = rec["scientificName"]
        index = rec["records"] / top_count
        tier = tier_for(index)

        # Effort correction: divide by the region's own monthly volume, then
        # rescale so the species' best month is 1.0.
        corrected = [rec["monthlyRecords"][i] / effort[i] for i in range(12)]
        peak = max(corrected)
        curve = [round(v / peak, 3) for v in corrected] if peak else [0.0] * 12

        name = overrides.get(sci) or rec["commonName"] or sci
        if "/" in name:
            warnings.append(f"unresolved slash-form name for {sci}: {name!r} "
                            f"-- add it to name_overrides.json")
        elif name == sci:
            warnings.append(f"no vernacular name for {sci} ({rec['records']} "
                            f"records); falling back to the scientific name")

        species.append({
            "speciesKey": rec["speciesKey"],
            "scientificName": sci,
            "commonName": name,
            "family": rec["family"],
            "order": rec["order"],
            "records": rec["records"],
            "reportingIndex": round(index, 4),
            "tier": tier,
            "deckEligible": tier not in DECK_INELIGIBLE,
            "seasonality": {
                "pattern": classify_season(curve),
                "peakMonth": curve.index(max(curve)) + 1,
                "monthly": curve,
            },
        })

    species.sort(key=lambda s: -s["records"])

    # 4. Did the birds we know are there actually come back?
    present = {s["scientificName"] for s in species}
    for sci in EXPECT.get(args.gadm, []):
        if sci not in present:
            warnings.append(f"EXPECT miss: {sci} is absent -- likely a GBIF "
                            f"backbone problem, not a real absence")
    if args.gadm not in EXPECT:
        warnings.append(f"no EXPECT list for {args.gadm}; add one before "
                        f"trusting this output")

    tier_counts = {name: sum(1 for s in species if s["tier"] == name)
                   for name, _ in TIERS}
    eligible = sum(1 for s in species if s["deckEligible"])

    out = {
        "region": {"slug": args.slug, "name": args.name, "gadmGid": args.gadm},
        "source": {
            "provider": "GBIF",
            "datasetKey": EBIRD_DATASET_KEY,
            "dataset": "eBird Observation Dataset",
            "years": list(years),
            "totalRecords": total_records,
            "monthlyRecords": effort,
            # What fraction of the year's birding happens in each month. Kept so
            # a consumer can see how much correction was applied.
            "monthlyEffortShare": [round(e / total_records, 4) for e in effort],
        },
        "method": {
            "reportingIndex": "record count / most-reported species in region; "
                              "a relative index, not % of checklists",
            "seasonality": "monthly counts / region monthly record volume, "
                           "rescaled so the species' best month is 1.0",
            "tierThresholds": {name: floor for name, floor in TIERS},
        },
        "speciesCount": len(species),
        "deckEligibleCount": eligible,
        "tierCounts": tier_counts,
        "species": species,
    }

    path = args.out or os.path.join(DATA_DIR, f"{args.slug}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    print(f"\n{len(species)} species, {eligible} deck-eligible")
    for name, _ in TIERS:
        print(f"  {name:<11} {tier_counts[name]:>4}")
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    print(f"\nwrote {path} in {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
