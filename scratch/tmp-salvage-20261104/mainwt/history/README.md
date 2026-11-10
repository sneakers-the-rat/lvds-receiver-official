# Routing history snapshots

This directory is the project's routing memory, kept in the repo
forever, rendered by the Jekyll site (website/, collection
`_passes/`) as the Routing history pages. Intermediate and failed
attempts are kept on purpose — the evolution is the story.

Since 2026-11-04 the organising record is the **pass log**: one
monotonic counter (pass 1, 2, 3, …) over committed board states.
See `PASSES.md`. The older per-attempt snapshots below remain as the
render source for passes 1–10; `index.json` is frozen as the legacy
record of that era and is no longer updated or read by the site.

## Layout

- `PASSES.md` — the pass log (human-readable): the numbering rule,
  one changelog entry per pass, the gaps (runs never committed, so
  never numbered), and the reconciliation with the provisional
  count that preceded it.
- `passes.json` — machine-readable twin of the pass log. This is
  what the site reads. Each entry: pass number, commit hash, UTC
  timestamp, board file, snapshot directory (if renders exist),
  audit stats ("not recorded" where never measured), and the
  one-line changelog description of what strategy changed.
- `pass-NNNN/` — one snapshot directory per pass from pass 11 on,
  created by `scripts/commit_pass.py`: the same file set as the
  legacy snapshots (renders + `stats.txt`) plus `audit.txt`, the
  pass's own audit output.
- `index.json` — LEGACY machine-readable list of pre-pass-system
  attempts (timestamp, commit hash, label, stats, note), sorted
  chronologically. Frozen; superseded by `passes.json`.
- `<UTC-timestamp>_<short-hash>/` — one snapshot per pre-pass-system
  attempt (these are the render directories passes 1–10 point at):
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

## Adding a pass (the convention)

One command, from the repo root, the moment a run produces a new
board state — a finished run, a checkpoint of a long run, a
placement change:

```sh
python3 scripts/commit_pass.py "what changed in this pass"
```

It runs the audit (`hw/check_pcb.py`) on the board and saves it as
`history/pass-NNNN/audit.txt`, renders the pass's image set into
`history/pass-NNNN/` with the route-only machinery below, appends
the entry to `PASSES.md` + `passes.json` with the next number,
stages exactly the pass's files (board, router code and results
changes under `hw/`/`results/`, the pass directory, the log files)
and commits with subject `pass NNNN: <description>`. A commit
cannot contain its own hash, so the command then makes one small
bookkeeping commit (`pass NNNN: record commit hash`) writing the
pass commit's hash into the log. After the command, the only
remaining step is a push.

Options: `--board <file>` (audit + render a board other than
`hw/pdlvds_rx.kicad_pcb` — variant boards are passes too),
`--note "..."` (extra note on the entry), `--no-audit` (skip the
audit; stats are recorded as not recorded).

The old flow — `scripts/snapshot_route.py` into `index.json`, with
the snapshot committed separately after the attempt — is retired:
it made committing each render a two-step manual process, which is
how runs went uncommitted. `snapshot_route.py` remains in the tree
because `commit_pass.py` reuses its render machinery, and
`index.json` remains as the frozen record passes 1–10 were
backfilled from.
