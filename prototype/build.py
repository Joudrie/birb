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


def wrap(fragment):
    """Wrap the template fragment in a real HTML document.

    template.html is a fragment -- a <title>, a <style> and then content. That
    is what an embedding host wants, but a file served on its own needs the rest
    of the document, and the two omissions bite hard:

      no doctype   the browser falls into quirks mode
      no viewport  a phone assumes a ~980px desktop viewport and shrinks the
                   two-column layout to unreadable

    The template has exactly one <style> block, so splitting on its close tag
    puts the title and styles in the head and everything else in the body.
    """
    end = fragment.find("</style>")
    if end == -1:
        raise SystemExit("error: template.html has no <style> block to split on")
    end += len("</style>")
    head, body = fragment[:end].strip(), fragment[end:].strip()

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="color-scheme" content="light dark">\n'
        '<meta name="description" content="Clickable prototype of a birdwatching '
        'scrapbook: a closed, regional, seasonal set of 24 Massachusetts birds.">\n'
        f"{head}\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )


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
    out = wrap(template.replace(MARKER, blob))

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(out)

    print(f"{len(species)} species, {len(payload['deck']['order'])} deck cards")
    print(f"wrote {args.out} ({len(out) / 1024:.0f}K)")


if __name__ == "__main__":
    main()
