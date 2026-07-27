# Birdwatch — UI architecture

Screen-by-screen layout, navigation, and component system for v1.

Everything here is constrained by four decisions already made in the handoff, and
they do more design work than any style choice:

1. **The set is closed.** 24 cards, not an infinite life list. Completion exists.
2. **It's a scrapbook.** Your photo is the content. The reference image is a footnote.
3. **No AI identification.** You tell the app what you found.
4. **Local-first and private.** No account, no feed, no published sightings.

## One deviation from the brief

You asked for a **Map / Discovery Portal** as a core pillar. A map of *other
people's* sightings is the one thing this app deliberately isn't — it's eBird's
product, it requires a backend, and it breaks the privacy story that is the
reason to choose this over Merlin. And "discovery" implies an unbounded world to
explore, which is the opposite of a closed set.

So the map survives as a **view mode inside your own Journal** — your pins, your
phone, nobody else's — and the home pillar is the **Deck** instead. The deck grid
is the screen that carries `11 / 12 rare birds`, and that feeling is the product.
Everything below assumes that swap.

---

## 1. Global navigation

Four tabs, plus one persistent action.

```
┌──────────────────────────────────────────────┐
│                                              │
│                 (screen)                     │
│                                              │
│                              ╭─────╮         │
│                              │  📷 │  ← FAB  │
│                              ╰─────╯         │
├──────────────────────────────────────────────┤
│   ◈        ▤        ☰        ◐               │
│  Deck   Journal   Codex   Region             │
└──────────────────────────────────────────────┘
```

| Tab | Axis | Answers |
|---|---|---|
| **Deck** (home) | the closed set | *What's left to find?* |
| **Journal** | time | *What have I done?* |
| **Codex** | taxonomy | *What exists here at all?* |
| **Region** | place & config | *Where am I birding, and what else could I play?* |

Deck and Codex are deliberately separate. The deck is 24 curated cards you can
finish; the codex is all 420 Massachusetts species including the 152 vagrants
that are never dealt. Collapsing them would reintroduce the infinite list.

**Profile is not a tab.** There is no social graph to profile — no followers,
no leaderboard, no shared identity. What a profile tab would have held (region,
settings, export, credits) lives in **Region**, which has actual work to do.

The **FAB is global** — it floats above every tab. Logging must never require
navigating first.

---

## 2. Screen layouts

### 2.1 Deck — home

```
┌──────────────────────────────────────────────┐
│  Backyard 24                        ⌄ July   │  collapsing large title
│  Massachusetts                               │  + month chip → calendar
├──────────────────────────────────────────────┤
│                                              │
│              10 / 24 found                   │  HERO
│   ▓▓▓▓▓▓░░  ▓▓▓░░░░░  ▓░░░░░  ░░             │  segmented, one per tier
│   6/8       3/8       1/6     0/2            │
│   common   uncommon   rare   super rare      │
│                                              │
├──────────────────────────────────────────────┤
│  HERE NOW, NOT YET YOURS               →     │  horizontal scroll
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐                 │  driven by seasonality
│  │ ?  │ │ ?  │ │ ?  │ │ ?  │                 │
│  └────┘ └────┘ └────┘ └────┘                 │
│  Catbird Oriole Waxwing Grosbeak             │
├──────────────────────────────────────────────┤
│  COMMON                          6 / 8       │
│  ┌────────┐ ┌────────┐                       │
│  │ [your  │ │ [your  │      2-col grid       │
│  │  photo]│ │  photo]│      3-col on tablet  │
│  │Blue Jay│ │Chickad.│                       │
│  └────────┘ └────────┘                       │
│  ┌────────┐ ┌────────┐                       │
│  │   ◭    │ │   ◭    │                       │
│  │ Robin  │ │Cardinal│                       │
│  └────────┘ └────────┘                       │
│                                              │
│  UNCOMMON                        3 / 8       │
│  …                                           │
│  RARE                            1 / 6       │
│  …                                           │
│  SUPER RARE                      0 / 2       │
│  …                                           │
└──────────────────────────────────────────────┘
```

**The card has three states, and getting them right is the whole screen.**

| State | Render | Reads as |
|---|---|---|
| **Found** | your photo fills the card, name plate below, small date | a filled scrapbook page |
| **Findable now** | silhouette on paper, tier-coloured border, name | *go get this* |
| **Out of season** | dimmed silhouette, no border, `back in October` | *coming later* |

The third state is the retention mechanic made visible. It must never read as a
failure or a lock — no padlock icon, no grey-out-as-punishment. It's an
anticipation state, phrased in months, not in absence.

The data supports this exactly. In the Massachusetts Backyard 24:

- **January** — 18 of 24 findable. The six summer birds (Catbird, Oriole,
  Waxwing, Hummingbird, Grosbeak, Tanager) are simply not in the state.
- **May** — 23 of 24. The Dark-eyed Junco has gone north.
- **No single month contains all 24.**

That last line is a stronger design fact than the handoff assumed, and it should
be surfaced, not hidden: finishing this deck **requires birding in at least two
seasons**. The deck header can say so once, plainly, when a player first opens
it — "This set can't be finished in one season. That's the point."

### 2.2 Journal

```
┌──────────────────────────────────────────────┐
│  Journal                              ⌕      │
│  37 sightings · 14 species                   │
├──────────────────────────────────────────────┤
│  [ List ]  [ Map ]  [ Calendar ]             │  segmented control
├──────────────────────────────────────────────┤
│  TODAY                                       │
│  ┌──┐ Northern Cardinal          ● rare      │
│  │▩ │ 7:42 AM · Back garden                  │
│  └──┘                                        │
│  ┌──┐ Blue Jay                   ● common    │
│  │▩ │ 7:38 AM · Back garden                  │
│  └──┘                                        │
│                                              │
│  SATURDAY, 12 JULY                           │
│  ┌──┐ Gray Catbird               ● uncommon  │
│  │▩ │ 4:10 PM · Mount Auburn                 │
│  └──┘                                        │
└──────────────────────────────────────────────┘
```

- **List** — date-sectioned, reverse chronological. Each row: photo thumb,
  common name, time, place, tier pip. Tap → the sighting; long-press → edit.
- **Map** — your pins only, clustered by place. A one-line banner the first time:
  *"These pins never leave your phone."* Locations render at your chosen
  precision, not raw GPS.
- **Calendar** — a year grid of days you logged something. This is the scrapbook
  view: sparse in February, dense in May, and that shape is itself the story.

Filters: tier, species, month, has-photo.

### 2.3 Codex

The full regional list — everything GBIF knows about Massachusetts, including
what a deck will never deal you.

```
┌──────────────────────────────────────────────┐
│  ⌕ Search 420 Massachusetts birds            │
│  [All] [In my deck] [Logged] [By family]     │
├──────────────────────────────────────────────┤
│  COMMON                              32      │
│  ✓ Blue Jay                    ▁▂▃▅▇▅▃▂▁▂▃▄  │
│    Cyanocitta cristata          ●●●●         │
│  ✓ Black-capped Chickadee      ▇▇▅▃▂▂▁▂▃▄▅▆  │
│    Poecile atricapillus         ●●●●         │
│                                              │
│  UNCOMMON                            68      │
│  …                                           │
│  RARE                                81      │
│  SUPER RARE                          87      │
│                                              │
│  STRAYS & ESCAPEES                  152      │
│  Never dealt into a deck — but finding one   │
│  should be a delight.                        │
│    Painted Bunting              ○            │
│    Egyptian Goose               ○            │
└──────────────────────────────────────────────┘
```

Each row carries a **12-bar micro season strip**, which is the cheapest possible
way to make 420 rows genuinely informative rather than a phone book.

Vagrants get their own section with an honest label. They're real records but not
*findable*, so they're excluded from decks — and saying that out loud is better
than silently hiding 152 species the data contains.

### 2.4 Region

```
┌──────────────────────────────────────────────┐
│  Region                                      │
├──────────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐    │
│  │  Massachusetts                       │    │
│  │  420 species · 268 deck-eligible     │    │
│  │  29.3M records, 2015–2026            │    │
│  │                          [ Change ]  │    │
│  └──────────────────────────────────────┘    │
├──────────────────────────────────────────────┤
│  YOUR DECKS                                  │
│  Backyard 24                    10 / 24  →   │
│  Coastal                        coming soon  │
│  Warbler Wave                   coming soon  │
│  Winter Visitors                coming soon  │
├──────────────────────────────────────────────┤
│  THIS MONTH IN MASSACHUSETTS                 │
│  Peak birding month. 20.7% of all records    │
│  in the state land in May.                   │
│  4 of your unfound birds are here now  →     │
├──────────────────────────────────────────────┤
│  Display & glare                        →    │
│  Location precision                     →    │
│  Back up & export                       →    │
│  Where the data comes from              →    │
└──────────────────────────────────────────────┘
```

"Where the data comes from" is a real screen, not an about-box: GBIF, the eBird
Observation Dataset, the year range, and the two honest caveats —
`reportingIndex` is a relative index and **not** "% of checklists", and
seasonality is effort-corrected but **not** habitat-corrected.

---

## 3. Bird Profile

The most important screen after the deck grid, and the one where most bird apps
make the same mistake: they lead with a stock reference photo. **Here your photo
is the hero and the reference is secondary** — that inversion is the scrapbook.

```
┌──────────────────────────────────────────────┐
│  ←                                    ⋯      │
│ ┌──────────────────────────────────────────┐ │
│ │                                          │ │  1. YOUR PHOTOS
│ │            [ your photo ]                │ │     full-bleed, paged
│ │                                          │ │     ● ○ ○   3 photos
│ └──────────────────────────────────────────┘ │     ↳ if none: empty
│                                              │       plate + "Add your
│  Northern Cardinal                           │  2.   first" and the
│  Cardinalis cardinalis                       │       reference behind a
│  Cardinalidae · Passeriformes                │       "Reference" label
│                                              │
│  ┌──────────┐  ┌────────────────────────┐    │  3. TIERS — both, always
│  │ ●●● Rare │  │ ●● Common in Mass.     │    │     deck tier ‖ regional
│  │ this deck│  │                        │    │     tap → why they differ
│  └──────────┘  └────────────────────────┘    │
├──────────────────────────────────────────────┤
│  WHEN IT'S HERE                              │  4. SEASONALITY
│                                              │     the distinctive view
│  ▇ ▇ ▆ ▅ ▄ ▃ ▃ ▃ ▄ ▅ ▆ ▇                     │
│  J F M A M J J A S O N D                     │
│      ▲ now                                   │
│                                              │
│  Year-round resident. Easiest in February,   │
│  when the leaves are down.                   │
│                                              │
│  ⓘ When it's reported, corrected for how     │
│    much people bird each month.              │
├──────────────────────────────────────────────┤
│  ▶  Song                          0:00 ─── │  5. AUDIO
│  ▶  Call                          0:00 ─── │     one row each
├──────────────────────────────────────────────┤
│  YOUR SIGHTINGS                        3     │  6. YOUR HISTORY
│  ┌──┐ 27 Jul 2026 · Back garden              │
│  │▩ │ "On the feeder at dawn"                │
│  └──┘                                        │
│  ┌──┐ 4 May 2026 · Mount Auburn              │
│  └──┘                                        │
│                                              │
│  You've seen it in:                          │
│  · · · ▪ ▪ · · · · · ▪ ·                     │  your months vs the
│  J F M A M J J A S O N D                     │  region's curve above
├──────────────────────────────────────────────┤
│         [  + Add a sighting  ]               │
├──────────────────────────────────────────────┤
│  Reference photo © … CC BY-SA 4.0            │  7. ATTRIBUTION
│  Song: xeno-canto XC… CC BY-NC 4.0           │     not optional
│  Occurrence data: GBIF / eBird               │
└──────────────────────────────────────────────┘
```

Notes on the sections that carry weight:

**3 — Both tiers, side by side.** A Baltimore Oriole is `rare` in this deck and
`uncommon` in Massachusetts, and showing both is what makes the deck tier feel
earned rather than arbitrary. The tap-through explains it in one sentence:
*"Ranked against the other 23 cards in this deck, not against all 420
Massachusetts birds."*

**4 — The season strip is the app's signature data view.** Twelve bars from
`seasonality.monthly`, current month marked, and a plain-English sentence
generated from `pattern` + `peakMonth`. The ⓘ line is the honesty note and
should not be buried — it's the difference between a claim we can defend and one
we can't.

**6 — Your months against the region's months.** The region's curve says when the
bird is here; your strip says when *you* were out. Seeing the gap is both a
scrapbook pleasure and, quietly, the best possible prompt to go birding in
November.

**7 — Attribution is structural, not decorative.** Reference photos and audio are
still blocked on licensing (Wikimedia / iNaturalist CC and xeno-canto are the
candidates; Macaulay Library is not freely licensable). The slots are designed
now so nothing ships without the credit line attached to it.

---

## 4. Quick-log

The field constraint: **one hand, glare, gloves, the bird is leaving.**

Target is **three taps, no typing, no menus**, and it works with no signal.

```
   FAB ──tap──▶ camera opens immediately
                (not a menu — the camera IS the tap)
                       │
                    shutter
                       │
                       ▼
   ┌──────────────────────────────────────────┐
   │   [ photo preview, dimmed ]              │
   │                                          │
   ├──────────────────────────────────────────┤
   │  What did you find?              ⌕       │
   │                                          │
   │  MOST LIKELY RIGHT NOW                   │  ← ranked by data:
   │  ◭  American Robin                       │    reportingIndex ×
   │  ◭  Song Sparrow                         │    how present it is
   │  ◭  Mourning Dove                        │    this month, over
   │  ◭  Northern Cardinal                    │    deck members not
   │  ◭  American Goldfinch                   │    yet logged
   │  ◭  Gray Catbird                         │
   │  ◭  Tufted Titmouse                      │    top 8 only
   │  ◭  Downy Woodpecker                     │
   │  More from your deck — 14           →    │  ← the tail, one tap
   │                                          │
   │  RECENT                                  │
   │  ✓  Blue Jay                             │
   │  ✓  Northern Cardinal                    │
   │                                          │
   │  ALL 420 MASSACHUSETTS BIRDS        →    │
   │                                          │
   │  📍 Back garden · ~1 km          ✕       │  auto, dismissible
   └──────────────────────────────────────────┘
                       │
                   tap a bird
                       │
                       ▼
              logged · one haptic tick
              card flips to your photo
```

**Why this beats an ID button.** The right answer is on screen without scrolling
most of the time, because the list is *ranked* rather than merely filtered.
That's the same convenience an AI ID would buy, from honest data, with no chance
of confidently naming the wrong bird — and without becoming the identification
app we said we weren't building.

**Ranking, not filtering — a correction from the prototype.** The first version of
this design filtered to "in the region this month, in your deck, not yet logged"
and assumed that left 4–10 birds. Building it proved otherwise: for a *new* player
in June, 22 of the 24 cards qualify, and a 22-row sheet is not a quick-log. The
filter only gets short once you have nearly finished the deck — exactly when you
need the help least.

So the sheet ranks by `reportingIndex × seasonality.monthly[thisMonth]` — how
likely you are to be photographing that bird *right now* — and shows the top 8,
with the remainder behind a single **More from your deck** row. In June that puts
American Robin, Song Sparrow, Mourning Dove and Northern Cardinal in the first
four rows, which is where the answer usually is. The promise is "the answer is
near the top", not "the list is short", and only the ranked version keeps it.

**Other entry points**

| Route | Taps | For |
|---|---|---|
| Long-press FAB → *Log without a photo* | 2 | heard it, or it flew |
| Bird Profile → *Add a sighting* | 2 | species already known |
| Photos share sheet → Birdwatch | 2 | a shot from earlier; date and place read from EXIF |
| Deck card → long-press → *I found this* | 2 | filling the grid deliberately |

**Field ergonomics**

- The species sheet is **bottom-anchored**; every control sits in the lower 40%
  of the screen. Nothing actionable in the top corners.
- Rows are **56 pt tall** with the tap target spanning full width.
- The sheet is **dismissible downward** but the photo is **never lost** — an
  un-speciesed photo goes to a small *Unfiled* tray in the Journal. Missing a bird
  because you fumbled the sheet would be the worst possible failure.
- **Everything above works offline.** The deck and species list are bundled JSON;
  photos and sightings are local. Cell service is bad where the birds are.

**Location**

Auto-captured, never required, and coarse by default. Three settings: *Precise*,
*Approximate (~1 km, default)*, *Place name only*, *Off*. Nothing is transmitted
anywhere — the setting governs what's written to your own database, so an
exported scrapbook doesn't leak your house.

---

## 5. Design language & accessibility

### Themes — three, not two

Dark mode is the wrong answer to sunlight. Outdoors at noon you want **maximum
luminance contrast**, which means a light theme with the contrast pushed up, not
a dark one.

| Theme | When | Character |
|---|---|---|
| **Paper** | default, indoors | warm off-white, soft shadows, serif species names |
| **Night** | evening, dawn chorus | true dark, dimmed photos, no pure-white text |
| **Field** | bright sun | pure white ground, near-black text, heavier weights, thicker strokes, no opacity-based greys, +1 type size |

Auto-switch on the ambient light sensor, with a manual override that sticks.
**Field mode is a first-class theme**, not a filter — components declare their
Field variants, because thin 1 px hairlines and 60 %-opacity captions simply
disappear in sun.

### Tier encoding — never colour alone

Tier is the app's primary data dimension, so it gets three redundant encodings:

```
common      ● ○ ○ ○   slate
uncommon    ● ● ○ ○   sage
rare        ● ● ● ○   amber
super rare  ● ● ● ●   terracotta
vagrant     ◌         violet, outline only
```

Pips + colour + label. All chips clear 4.5:1 against all three theme grounds.
A colourblind player loses nothing.

### The signature number

`11 / 12 rare birds` is the product's core feeling, so it gets one fixed
typographic treatment used everywhere it appears — deck hero, section headers,
tier chips:

```
   11 / 12  RARE BIRDS
   ▲   ▲    ▲
   │   │    └ small caps, tracked, tier colour
   │   └ light weight, 60% of numerator size
   └ heavy weight, tabular figures
```

Tabular figures matter: the number changes as you log, and digits must not jitter.

### Component system

Card-based, but *card* here means **scrapbook page**, not Material surface —
paper texture, soft physical shadow, a slight plate inset around your photo.

| Component | Variants |
|---|---|
| `SpeciesCard` | found · findable · out-of-season |
| `TierChip` | deck tier · regional tier · compact pip |
| `SeasonStrip` | micro (codex row) · full (profile) · personal-overlay |
| `CompletionMeter` | segmented by tier · single-tier inline |
| `SightingRow` | with photo · without photo · unfiled |
| `SpeciesPickerSheet` | shortlist · search · full codex |
| `PhotoPlate` | your photo · reference (always labelled) · empty |
| `AttributionFooter` | photo · audio · data |

Every component that shows someone else's image or audio takes an attribution
prop that cannot be omitted. Licensing gets enforced by the type system rather
than by remembering.

### Motion and reward

**One** moment of delight: when a card flips from silhouette to your photo, it
presses down like a passport stamp — a 220 ms scale-and-settle, one soft haptic.
That's it.

No confetti. No points tallying up. No streak counters. No level-up. The reward
is the grid filling in, and adding a second reward layer on top would turn a
scrapbook into the game we explicitly aren't making.

### Accessibility

- **Dynamic Type to XXL** without clipping. The 2-column grid reflows to 1
  column at accessibility sizes; the season strip keeps its bars and drops its
  month letters to a VoiceOver-only label.
- **VoiceOver reads data as sentences.** The season strip announces *"Summer
  visitor. Here from May to September, easiest in June."* — not twelve numbers.
  The deck hero announces *"Ten of twenty-four found. Rare: one of six."*
- **Reduce Motion** removes the stamp press; the card cross-fades instead.
- **48 × 48 pt minimum** targets, 64 pt FAB.
- **No time-limited interactions** anywhere. Nothing expires, nothing is missed
  by being slow.
- **Photos carry alt text** you can write, and the species name is the default.

### Anti-patterns, stated so they don't creep back in

No streaks · no daily-login nag · no leaderboards · no friend feed · no
share-prompt after logging · no "identify this bird with AI" button · no
unbounded life list · no account required · no sighting ever leaves the device
unless the user explicitly exports it.

---

## 6. Data & state architecture

v1 needs no backend at all.

```
bundled, read-only            on device, user-owned
──────────────────            ─────────────────────
data/us-ma.json               sightings   (SQLite)
  420 species                   id, speciesKey, timestamp,
  tiers, seasonality            lat, lon, precision, note
data/deck-us-ma-             photos      (app sandbox)
  backyard-24.json              assetId → sightingId
  24 cards                    settings    (key/value)
```

**Progress is derived, never stored.** `found` is a join between `sightings` and
the deck's `speciesKey` list — computed on read. There is no separate progress
record to drift out of sync, no migration when a deck is re-curated, and
re-running the pipeline can't corrupt anyone's scrapbook.

`speciesKey` (the GBIF integer) is the join key everywhere, not the common name
— names change, and this project already has eleven of them overridden.

**Export** is a zip: original photos plus a JSON manifest. That's the backup
story, the device-migration story, and the "it's yours" story, all in one file.

---

## 7. What this design is still blocked on

- **Reference photos and audio.** Wikimedia Commons / iNaturalist CC and
  xeno-canto are the candidates. The slots and the attribution components are
  designed; the licences aren't resolved. Nothing ships in those slots until
  they are.
- **Habitat is not in the data.** Deck curation is currently the only thing
  encoding *where* a bird is findable, so the shortlist in the quick-log sheet
  can order by season but not by "you are standing in a saltmarsh." Making
  habitat real data would improve that sheet more than any UI change.
- **State granularity.** The Berkshires and Cape Cod share a `reportingIndex`
  and shouldn't. County GADM ids are a drop-in pipeline change; the UI already
  routes through a region object, so it costs nothing here.
