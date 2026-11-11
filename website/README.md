# Project site (Jekyll)

The site skeleton is Jekyll; this directory is the source. It
replaced the hand-rolled `scripts/build_site.py` generator on
2026-11-04 (user directive: a real static-site tool, a left-bar
table of contents, and content as files so iteration — e.g. each
relayout — is just adding a file).

## Build

From the repo root:

    python3 scripts/site_data.py     # data + asset staging step
    cd website && bundle exec jekyll build

Output lands in `../site/` (the directory CI uploads as the Pages
artifact). CI's build-site job runs the same two steps after
downloading the validation jobs' artefacts; the validation jobs and
their gates are untouched by the site build.

## Layout of the source

- `_layouts/default.html` — page frame with the persistent **left
  sidebar table of contents** (all sections + every pass page).
- `_layouts/pass.html` — one layout pass: stats table, ADOPTED
  badge, stacked + per-layer route renders, prev/next links.
- `_includes/sidebar.html` — the TOC. Sections are hard-coded links;
  the pass list is a Liquid loop over the collection, so it never
  needs editing when a pass is added.
- `_includes/status_panel.html` — the build-status panel, rendered
  from `_data/status.json`.
- `_passes/pass-NNNN.md` — **one markdown file per layout pass**
  (Jekyll collection). Front matter: pass number, commit hash, UTC
  timestamp, audit stats, adopted flag, render file map. Body: the
  changelog description.
- `index.md`, `build.md`, `board.md`, `tokens.md`, `routing.md`,
  `progress.md`, `schematic.md`, `stackup.md`, `bom.md`,
  `sims.md`, `testplan.md`, `downloads.md` — the site's pages.
  `design.md` and `requirements.md` are thin wrappers that stage
  `docs/02` / `docs/01` (see `_includes/docs/` below); `build.md`
  likewise stages the build guide from `docs/14`. `routing.md`
  lists the passes with a Liquid loop over the collection.
- The board page and the landing page embed an interactive 3D
  model (`assets/gen/board-3d.glb`, staged by the data step)
  through Google's `<model-viewer>` element, vendored at
  `assets/js/model-viewer.min.js` — no CDN dependency at runtime.
- `_plugins/filters.rb` — `number_delimiter` and `pacific`
  (timestamps are stored UTC and displayed in America/Los_Angeles).
- `_data/layers.yml` — copper-layer order + palette (keep in sync
  with `scripts/snapshot_route.py`).

## Data step

`scripts/site_data.py` (the only Python left in the site path) runs
before `jekyll build` and writes the generated, gitignored files:

- `_data/status.json` — CI job rows (from `.site-status/`, CI-only)
  and per-check verdicts from `results/`, including the DRC
  board-state wording against `ci/drc-baseline.json`. It displays
  the gates' numbers; the gates themselves are
  `scripts/drc_gate.py` / `scripts/erc_gate.py`, unchanged.
- `_data/tokens.json` — token totals computed from the committed
  `metrics/*.csv` export; `_data/costs.json` — the cost tables
  (rates from `metrics/api_rates.json`; tier-matched, upper-bound
  and cache-adjusted costs from `metrics/cost_summary.csv`),
  staged when those files exist (the token page's Cost section
  renders only then).
- `_data/bom.json`, `_data/sims.json`, `_data/board.json`,
  `_data/downloads.json` — BOM table, simulation blocks, asset
  presence, download list.
- **Current-info pages are regenerated at build time, never
  staged from a hand-refreshed copy.** The board renders (and
  the board-layers PDF) are exported by the data step from the
  current frontier board — the newest
  `hw/pdlvds_rx.exp<N>.kicad_pcb`, selected by
  `commit_pass.resolve_board` (`SITE_BOARD=<path>` overrides,
  for testing); the schematic SVG and PDF are exported from the
  current schematic the same way; the BOM is rebuilt from a
  netlist exported from that schematic. Where a build has no
  KiCad (CI's build-site job), staging falls back to `hw/fab/` —
  which CI's kicad-validate job regenerates from the same
  frontier board on every run (`scripts/make_fab.sh`, shipped as
  the fab-outputs artefact) — and `board.json` records which
  path produced each asset; the board/BOM/schematic/downloads
  pages print that provenance. The simulation blocks are the one
  display-only input: the sims are not re-run by the site build
  (CI's sim job refreshes `results/`), and the sims page shows
  each result file's update time.
- `assets/gen/`, `downloads/` — staged copies of the fab
  downloads, results plots, metrics charts and per-pass history
  renders (the history renders are committed per-pass records and
  are never re-rendered).
  Board render SVGs (fab top/bottom/composite/per-layer and the
  per-pass history renders) get a full-canvas `#111` background
  rect baked in at this step (`inject_svg_background()` in
  `site_data.py`, marker `id="site-bg"`): KiCad's exports carry no
  background, so a render opened on its own — the board page's
  gallery opens the big view in a new tab — would otherwise lose
  the dark panel the CSS paints behind it on the page. Sources in
  `hw/fab/` and `history/` are never modified.
- The board page's Routes section is a selectable gallery
  (`board.md` + `assets/js/routes-gallery.js`): thumbnails for the
  all-layers composite (`hw/fab/board-layers.svg`, staged like the
  other fab renders) and each copper layer; clicking one swaps the
  main viewer, and the viewer image links to the shown SVG in a
  new tab. Without JavaScript the thumbnails are plain links.
- The interactive 3D model is exported by the data step with
  `scripts/export_glb.sh` (KiCad required): it renders a copy of
  the frontier board with `kicad-cli pcb export glb
  --subst-models`, resolving every footprint's model against the
  repo's own model mirror in `hw/models3d/` (library STEP/VRML
  files plus project-authored solids from
  `scripts/gen_models3d.py`, bound to the custom footprints by
  `scripts/attach_models.py`). Without KiCad it falls back to the
  fab package's `hw/fab/board-3d.glb` (which `scripts/make_fab.sh`
  refreshes the same way); `board.json`'s `model3d_source`
  records which path produced it, and the model is also staged
  as a download.
- `_includes/docs/` — `docs/01`, `docs/02`, `docs/05`, `docs/14`
  copied in (heading levels shifted one deeper); committed, and
  regenerated by the step, so a bare `jekyll build` also works.

Anything missing becomes an explicit "not available / not run"
placeholder, exactly as the old generator behaved — never a faked
value.

## Adding a layout pass

Use the one-command flow; it writes the markdown file for you:

    python3 scripts/commit_pass.py "what changed in this pass"

That audits and renders the board into `history/pass-NNNN/`,
appends `history/passes.json` + `history/PASSES.md`, writes
`website/_passes/pass-NNNN.md` from the same entry
(`scripts/gen_pass_pages.py`), and commits. The sidebar and the
routing index pick the new pass up automatically on the next build.
To regenerate the pass pages for the whole log by hand:
`python3 scripts/gen_pass_pages.py`.
