#!/usr/bin/env python3
"""Turn a curated species list into a playable deck.

Deck membership is editorial -- decks/*.json is a hand-written list of
scientific names. This attaches the numbers from the region dataset.

Deck tiers are assigned by rank *within the deck*, not by regional tier. A
Baltimore Oriole is only `uncommon` against all 420 Massachusetts birds, but
inside a 24-card backyard set it is one of the hardest cards, and that is the
number the player should see. Ranking within the deck also guarantees a real
difficulty curve rather than 22 easy cards and two impossible ones. Both live on
the card, as `tier` and `regionalTier`.

Usage:
    python3 build_deck.py --region us-ma --deck backyard-24
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_DIR = os.path.join(ROOT, "data")
DECK_DIR = os.path.join(ROOT, "decks")

TIER_ORDER = ["common", "uncommon", "rare", "super_rare"]

# A card counts as findable in a month when its effort-corrected curve is at
# least this fraction of its own best month. Used only to describe the deck's
# seasonal shape -- it gates nothing.
FINDABLE = 0.25

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]


def load(path, what):
    if not os.path.exists(path):
        sys.exit(f"error: no {what} at {path}")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def split_by_shape(ranked, shape):
    """Cut a reportingIndex-ordered list into deck tiers."""
    cards, at = [], 0
    for tier in TIER_ORDER:
        take = shape.get(tier, 0)
        for species in ranked[at:at + take]:
            cards.append((tier, species))
        at += take
    if at != len(ranked):
        sys.exit(f"error: tierShape sums to {at} but the deck has "
                 f"{len(ranked)} species")
    return cards


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True, help="region slug, e.g. us-ma")
    ap.add_argument("--deck", required=True, help="deck slug, e.g. backyard-24")
    ap.add_argument("--out", default=None, help="output path")
    args = ap.parse_args()

    region = load(os.path.join(DATA_DIR, f"{args.region}.json"), "region dataset")
    deck = load(os.path.join(DECK_DIR, f"{args.deck}.json"), "deck")

    if deck.get("region") and deck["region"] != args.region:
        sys.exit(f"error: deck {args.deck} is for region {deck['region']}, "
                 f"not {args.region}")

    index = {s["scientificName"]: s for s in region["species"]}

    picked, problems = [], []
    for sci in deck["species"]:
        species = index.get(sci)
        if species is None:
            problems.append(f"{sci} is not in {args.region} -- check the "
                            f"spelling, or it may have dropped out of GBIF's "
                            f"backbone entirely")
        elif not species["deckEligible"]:
            problems.append(f"{sci} is {species['tier']} and not deck-eligible; "
                            f"nobody could complete a set containing it")
        else:
            picked.append(species)
    if problems:
        for p in problems:
            print(f"error: {p}", file=sys.stderr)
        sys.exit(1)

    seen = {s["scientificName"] for s in picked}
    if len(seen) != len(picked):
        sys.exit("error: the deck lists the same species twice")

    picked.sort(key=lambda s: -s["reportingIndex"])

    shape = deck.get("tierShape")
    if not shape:
        sys.exit("error: deck has no tierShape; deck tiers are a curation "
                 "decision, so the shape has to be stated")

    cards = []
    for rank, (tier, species) in enumerate(split_by_shape(picked, shape), 1):
        cards.append({
            "rank": rank,
            "speciesKey": species["speciesKey"],
            "scientificName": species["scientificName"],
            "commonName": species["commonName"],
            "family": species["family"],
            "order": species["order"],
            "tier": tier,
            "regionalTier": species["tier"],
            "reportingIndex": species["reportingIndex"],
            "records": species["records"],
            "seasonality": species["seasonality"],
        })

    # How many cards are realistically gettable each month. This is what makes
    # the deck impossible to finish in January and finishable in June.
    by_month = [sum(1 for c in cards
                    if c["seasonality"]["monthly"][m] >= FINDABLE)
                for m in range(12)]
    complete_months = [MONTH_NAMES[m] for m in range(12)
                       if by_month[m] == len(cards)]

    out = {
        "deck": {
            "slug": deck["slug"],
            "name": deck["name"],
            "blurb": deck.get("blurb", ""),
            "region": region["region"],
            "size": len(cards),
            "tierShape": shape,
        },
        "source": {
            "builtFrom": f"data/{args.region}.json",
            "provider": region["source"]["provider"],
            "dataset": region["source"]["dataset"],
            "years": region["source"]["years"],
        },
        "method": {
            "tier": "rank within this deck by reportingIndex, cut by tierShape",
            "regionalTier": f"the species' tier across all "
                            f"{region['speciesCount']} {region['region']['name']} birds",
            "findableThreshold": FINDABLE,
        },
        "seasonalShape": {
            "cardsFindableByMonth": by_month,
            "completableIn": complete_months,
        },
        "cards": cards,
    }

    path = args.out or os.path.join(DATA_DIR, f"deck-{args.region}-{args.deck}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    print(f"{deck['name']} -- {len(cards)} cards")
    for tier in TIER_ORDER:
        members = [c for c in cards if c["tier"] == tier]
        if not members:
            continue
        print(f"\n  {tier} ({len(members)})")
        for c in members:
            print(f"    {c['commonName']:<27} {c['reportingIndex']:.3f}  "
                  f"{c['regionalTier']:<10} {c['seasonality']['pattern']}")
    print("\n  cards findable by month")
    for m in range(12):
        print(f"    {MONTH_NAMES[m]:<10} {by_month[m]:>2} / {len(cards)}")
    print(f"\n  completable in: "
          f"{', '.join(complete_months) if complete_months else 'no single month'}")
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
