# Routing history snapshots

This directory is the project's routing memory: one subdirectory per
routing attempt, kept in the repo forever, rendered by
`scripts/build_site.py` as the site's "Routing history" gallery.
Intermediate and failed attempts are kept on purpose — the evolution
is the story.

## Layout

- `index.json` — machine-readable list of attempts (timestamp, commit
  hash, label, stats, note), sorted chronologically. This is what the
  site reads.
- `<UTC-timestamp>_<short-hash>/` — one snapshot per attempt:
  - `board-top.svg`, `board-bottom.svg` — kicad-cli renders
    (copper + silk layers), when a board exists for the attempt;
  - `layer-FCu.svg`, `layer-In1Cu.svg`, `layer-In2Cu.svg`,
    `layer-BCu.svg` — single-layer exports, one per copper layer,
    each recoloured to the fixed palette below. All four share the
    board's viewBox, so they register pixel-perfectly when stacked;
  - `stats.txt` — the same numbers as the index entry, human-readable.
    Anything never measured is written as `not recorded`.

## Route-only renders (no zone fills)

All renders — per-layer, composite, and the top/bottom references —
show **routes only**: tracks, vias and pads. The opaque zone fills
(the GND pours) are removed, because a filled front pour hides every
layer beneath it. The snapshot script does this without touching
the committed board: it loads the board with `pcbnew` into a temp
copy, **deletes every zone in the temp copy**, saves that, and runs
all `kicad-cli` exports against the temp copy. The method is
recorded in each snapshot's `stats.txt` and in the index entry's
`render_method`.

Why deletion rather than `ZONE.SetIsFilled(False)`: that flag was
tried first and does not work — it persists in the saved board, but
KiCad 7's plotter draws the zones' stored filled polygons anyway
(F.Cu export byte size unchanged, 830,046 → 830,055). Deleting the
zones works, verified numerically: the largest filled F.Cu shape
drops from 7,821 mm² (the pour, 87% of the board) to 10 mm² (a
pad), with tracks and footprints intact. Silkscreen is excluded
from the per-layer and composite views; it appears only in the
top/bottom reference renders.

## Layer colours (fixed palette)

| Layer  | Colour    | Meaning        |
|--------|-----------|----------------|
| F.Cu   | `#FF3B30` | front copper   |
| In1.Cu | `#FF9500` | inner 1 (GND)  |
| In2.Cu | `#34C759` | inner 2        |
| B.Cu   | `#0A84FF` | back copper    |

Presentation is **light-on-dark** — the project owner's stated
preference (2026-11-03). Every render in the site gallery sits on
a `#111` panel: the composite stacks the four layer SVGs with
`mix-blend-mode: screen` at 0.55 opacity on that panel, and the
individual layer panels and the top/bottom reference renders sit
on the same dark panels with a subtle border.

To keep everything visible on dark, the snapshot script recolours
each export after rendering:

- layer geometry → the palette colour above (in the single-layer
  exports, and in the top/bottom references, where KiCad's muted
  per-layer theme colours `#C83434`/`#CE7D2C`/`#7FC87F`/`#4D7FC4`
  are mapped onto the same palette);
- drill holes, which KiCad draws `#FFFFFF`, → `#111111`, the
  panel tone, so a hole reads as a hole against the coloured pad
  around it instead of glowing;
- pure black `#000000` → `#9E9E9E` (verified to occur only in
  inert wrapper group styles — zero circles/paths in black groups
  across all exports — so nothing geometric changes);
- pads (`#ECECEC`) and silkscreen (`#F2EDA1`) are kept verbatim:
  both are clearly visible on dark.

The mapping is verified objectively after each regeneration: a
scan of every produced SVG finds zero fill/stroke colours with
relative luminance < 0.08 other than the designated panel tone
`#111111`. (Silkscreen and `#ECECEC` pads are absent from the
bottom references and from the unrouted placed board because the
raw KiCad exports themselves contain none there.)

`index.json` entries carry a `layers` map (layer name → file)
alongside `renders`.

## Making a snapshot (the per-attempt convention)

Commit the routing attempt first (board + audit results), then, from
the repo root:

```sh
python3 scripts/snapshot_route.py --label "router v6 — <what changed>"
```

The script takes the commit hash and timestamp from HEAD, renders
`hw/pdlvds_rx.kicad_pcb`, parses `results/pcb-audit.txt` and
`results/pcb_build.log` for stats, and updates `index.json`.
Re-running it for the same commit replaces that commit's entry
(idempotent). Commit the resulting `history/` changes with the next
commit.

Useful options:

- `--nets-routed N --nets-total 112 --pins-failed N` — explicit stats
  (they win over parsed ones).
- `--board <file>` — snapshot a board file other than the working one.
- `--hash <full> --timestamp <ISO>` — backfill an older attempt.
- `--no-board --note "..."` — record an attempt whose board was never
  committed (as v1/v2 here): the gallery shows the entry with an
  explicit no-render note.
