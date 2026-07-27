# Birdwatch — regional bird data

Data layer for the scrapbook birdwatching app: a finite, regional, tiered set of
birds you can go find and photograph. This directory covers **Massachusetts**.

Nothing here is app code yet. It's the dataset and the pipeline that builds it.

```
pipeline/fetch_region.py      GBIF -> a region's species, tiers, seasonality
pipeline/build_deck.py        a curated species list -> a playable deck
pipeline/name_overrides.json  North American common names GBIF gets wrong
decks/backyard-24.json        the curated Massachusetts starter set
data/us-ma.json               420 Massachusetts birds (generated)
data/deck-us-ma-backyard-24.json   the built deck (generated)
```

Rebuild everything:

```bash
cd pipeline
python3 fetch_region.py --gadm USA.22_1 --slug us-ma --name Massachusetts --top 420
python3 build_deck.py --region us-ma --deck backyard-24
```

Takes about 80 seconds. No API key, no dependencies beyond the standard library.

---

## Where the data comes from

**GBIF**, filtered to the eBird Observation Dataset. GBIF needs no API key and
its data is openly licensed, so this can ship commercially — which the eBird API
proper does not cleanly allow. Roughly 98% of the bird records GBIF returns for
a US state come from eBird anyway, so we read essentially the same observations
through a licence we can actually use.

Massachusetts: **29.3 million** bird records, 2015–2026.

## The two numbers that matter

### `reportingIndex` — how often a bird is actually reported

A species' record count as a fraction of the single most-reported bird in the
region. In Massachusetts that's the Blue Jay, so Blue Jay = 1.000 and
Black-capped Chickadee = 0.985.

This is **not** eBird's "% of checklists" frequency, and shouldn't be described
as such. GBIF gives no count of distinct checklists, so there's no denominator
for a true percentage. A relative index is all the tiering needs.

### `seasonality` — when it's here, corrected for birder effort

Raw monthly counts describe *birders*, not birds. Massachusetts birding is wildly
seasonal — May carries 20.7% of the year's records and February 5.2%, a 4×
swing — so on raw counts almost every species looks like a spring migrant.

Each species' monthly counts are divided by the region's own monthly record
volume, then rescaled so its best month is 1.0. What survives is genuine
seasonality. The classifier then labels each species `year_round`, `summer`,
`winter`, or `migrant`.

Spot-checks that came out right: Harlequin Duck and Snow Bunting `winter`;
Gray Catbird `summer`, peaking June; chickadee and titmouse `year_round`,
peaking February when leaves are down and feeders are busy.

## Rarity tiers

Thresholds on `reportingIndex`:

| Tier | Index | Meaning | n |
|---|---|---|---|
| `common` | ≥ 0.25 | you'll see it without trying | 32 |
| `uncommon` | 0.06 – 0.25 | a good walk in the right habitat | 68 |
| `rare` | 0.015 – 0.06 | you go looking for it | 81 |
| `super_rare` | 0.002 – 0.015 | a genuinely lucky day, but findable | 87 |
| `vagrant` | < 0.002 | off-course strays and escaped captives | 152 |

**The `vagrant` floor is a design decision, not a statistical one.** Below
~0.002 the tail stops being rare birds and becomes noise: one-record vagrants
(Northern Wheatear, Painted Bunting) and escaped captives (Egyptian Goose, Red
Junglefowl, Swan Goose). Those are real records, but they aren't *findable*, and
a tier nobody can complete defeats the point of a set. They stay in the dataset —
finding one should be a delight — but `deckEligible` is false and they're never
dealt into a deck. 268 of 420 species are deck-eligible.

## Decks

Which birds belong in a "backyard" set is editorial — a judgement about habitat
and recognisability that no dataset makes for you. So `decks/*.json` is a
hand-written list of scientific names, and `build_deck.py` attaches the numbers.

**Deck tiers are assigned by rank within the deck, not by regional tier.** A
Baltimore Oriole is only `uncommon` against all 420 Massachusetts birds, but
inside a 24-card backyard set it's one of the hardest cards — and that's the
number the player should see. Ranking within the deck also guarantees a real
difficulty curve rather than 22 easy cards and two impossible ones. Both numbers
are kept on the card (`tier` and `regionalTier`).

### Massachusetts Backyard 24

Shape: 8 common / 8 uncommon / 6 rare / 2 super rare.

The eight easiest are year-round residents you can get in January. The middle
introduces a winter visitor (Dark-eyed Junco, White-throated Sparrow) so the set
teaches that some birds only exist here in the cold. The hard end — Baltimore
Oriole, Ruby-throated Hummingbird, Rose-breasted Grosbeak, Scarlet Tanager — is
spring-and-summer only.

That's deliberate: **a January player physically cannot finish the deck**, and
has a reason to still be playing in May. The seasonal lock is the retention
mechanic, and it costs nothing to build because the data already knows.

---

## Known data problems

**Cooper's Hawk is missing.** eBird moved it to genus *Astur*; GBIF's backbone
marks *Astur* as DOUBTFUL, so those records fail to match and drop out. GBIF has
**zero** Massachusetts eBird records for a hawk that nests in suburban yards,
while Sharp-shinned Hawk has 31,817. It's left out of the Backyard 24 rather
than faked.

Nothing about the output *looks* wrong when this happens — the species is simply
absent. So `fetch_region.py` asserts that a short list of birds which certainly
occur in the region actually came back, and warns if not. Extend `EXPECT` when
adding a region. American Goshawk is affected by the same *Astur* move (166
records, well into vagrant territory).

**GBIF vernacular names are global, not North American.** Mostly it gets US
names right — of 38 spot-checked common Massachusetts species, only *Circus
cyaneus* was wrong ("Hen Harrier"). The rest of the fixes are lumped slash-forms
like "Green/Striated Heron" and "Snow/Ross's Goose". These can't be resolved
automatically: "Great Blue/Cocoi Heron" needs the trailing noun, while "Great
Cormorant/European Shag" must keep its own — same shape, opposite rule. So all
11 are written out in `name_overrides.json`, and the pipeline warns on any
surviving slash-form.

**Effort correction is not habitat correction.** The seasonality curve tells you
*when* a bird is around, not *where*. A saltmarsh sparrow and a feeder bird with
identical curves are not equally findable from your yard. Deck curation is
currently the only thing encoding habitat.

**State granularity is coarse.** The Berkshires and Cape Cod share a state and
almost nothing else. GBIF supports county-level GADM ids (`USA.22.X_1`), so
county decks are a drop-in change to `--gadm` when it's worth the fan-out.

## Not done yet

- Photos and audio (Wikimedia Commons / iNaturalist CC, xeno-canto) — licensing
  and attribution need resolving before anything ships.
- More decks: Coastal, Warbler Wave, Winter Visitors.
- More regions — the pipeline is already region-agnostic; only `EXPECT` and any
  new name overrides are per-region.
