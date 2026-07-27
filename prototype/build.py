#!/usr/bin/env python3
"""Build the clickable prototype into a single self-contained HTML file.

The prototype has to run from a file:// URL and from any static host, so it
cannot fetch the region JSON at runtime. This inlines a trimmed copy of it into
template.html instead.

Trimmed, not complete: the prototype needs a name, a tier, a reporting index and
a twelve-month curve per species, and nothing else. Rounding the curve to two
decimals costs nothing visible and roughly halves the payload.

Usage:
    python3 build.py                     # -> prototype/index.html
    python3 build.py --region us-ma --deck backyard-24
"""

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_DIR = os.path.join(ROOT, "data")
MARKER = "/*__DATA__*/"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", default="us-ma")
    ap.add_argument("--deck", default="backyard-24")
    ap.add_argument("--out", default=os.path.join(HERE, "index.html"))
    args = ap.parse_args()

    with open(os.path.join(DATA_DIR, f"{args.region}.json"), encoding="utf-8") as fh:
        region = json.load(fh)
    deck_path = os.path.join(DATA_DIR, f"deck-{args.region}-{args.deck}.json")
    with open(deck_path, encoding="utf-8") as fh:
        deck = json.load(fh)

    # A species' deck tier is what the player sees; its regional tier is the
    # context. Both travel with the card, so both get inlined.
    deck_tier = {c["scientificName"]: c["tier"] for c in deck["cards"]}

    species = []
    for s in region["species"]:
        row = {
            "n": s["commonName"],
            "s": s["scientificName"],
            "f": s["family"],
            "t": s["tier"],
            "i": s["reportingIndex"],
            "p": s["seasonality"]["pattern"],
            "k": s["seasonality"]["peakMonth"],
            "m": [round(v, 2) for v in s["seasonality"]["monthly"]],
        }
        if s["scientificName"] in deck_tier:
            row["d"] = deck_tier[s["scientificName"]]
        species.append(row)

    payload = {
        "region": region["region"],
        "counts": region["tierCounts"],
        "eligible": region["deckEligibleCount"],
        "total": region["source"]["totalRecords"],
        "effort": region["source"]["monthlyEffortShare"],
        "deck": {
            "name": deck["deck"]["name"],
            "shape": deck["deck"]["tierShape"],
            "order": [c["scientificName"] for c in deck["cards"]],
        },
        "species": species,
    }

    with open(os.path.join(HERE, "template.html"), encoding="utf-8") as fh:
        template = fh.read()
    if MARKER not in template:
        raise SystemExit(f"error: {MARKER} not found in template.html")

    blob = "const DB=" + json.dumps(payload, separators=(",", ":")) + ";"
    out = template.replace(MARKER, blob)

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(out)

    print(f"{len(species)} species, {len(payload['deck']['order'])} deck cards")
    print(f"wrote {args.out} ({len(out) / 1024:.0f}K)")


if __name__ == "__main__":
    main()
