# Clickable prototype

A single self-contained HTML file that runs the deck, the bird profile, the
codex and the three-tap quick-log on the real Massachusetts dataset. All 420
species, real rarity tiers, real effort-corrected seasonality.

**This is not app code.** It exists to make design decisions arguable before
anyone writes a line of the real thing.

```bash
cd prototype
python3 build.py          # -> index.html
open index.html           # no server needed
```

`build.py` inlines a trimmed copy of `data/us-ma.json` and
`data/deck-us-ma-backyard-24.json` into `template.html`. Edit `template.html`,
never `index.html` — the latter is generated and will be overwritten.

## What to try

**Scrub the month.** The control on the left is not an app feature; it's there
so you can move through the year and watch cards cross between *findable now*
and *out of season*. January offers 18 of 24, May offers 23, and no month offers
all of them. That seasonal lock is the retention mechanic, and it's the main
thing worth judging here.

**Log a bird.** The camera button opens the species sheet. There is no
identification — the sheet ranks by `reportingIndex × seasonality.monthly[month]`,
which is how likely you are to be photographing that bird right now, and shows
the top eight.

**Open a card in the codex.** Every one of the 420 species has a profile, not
just the 24 in the deck, including the 152 vagrants that are never dealt.

## What it found

The quick-log sheet originally filtered rather than ranked, on the assumption
that "in the region this month, in your deck, not yet logged" would leave four
to ten birds. Building it proved otherwise: for a new player in June, 22 of the
24 cards qualify. The filter only gets short once the deck is nearly finished,
which is when the help is least needed. Ranking fixed it. See `design/app-ui.md`.

## Honest limits

- **Card art is generated from the species name.** No photographs are used.
  Reference photo and audio licensing is still unresolved, so the audio rows are
  deliberately marked as blocked rather than faked.
- **Progress is in-memory** and resets on reload. The real app stores sightings
  on device.
- **Places are stubbed.** Every sighting says "Back garden".
