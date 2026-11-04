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
- `index.md`, `board.md`, `tokens.md`, `routing.md`,
  `schematic.md`, `stackup.md`, `bom.md`, `sims.md`, `testplan.md`,
  `downloads.md` — the site's pages, one per section of the old
  single-page site. `routing.md` lists the passes with a Liquid
  loop over the collection.
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
  `metrics/*.csv` export; `_data/costs.json` — `metrics/
  cost_summary.csv` staged verbatim when that file exists (the
  token page's Cost section renders only then).
- `_data/bom.json`, `_data/sims.json`, `_data/board.json`,
  `_data/downloads.json` — BOM table, simulation blocks, asset
  presence, download list.
- `assets/gen/`, `downloads/` — staged copies of fab renders,
  results plots, metrics charts and per-pass history renders.
- `_includes/docs/` — `docs/01`, `docs/02`, `docs/05` copied in
  (heading levels shifted one deeper); committed, and regenerated
  by the step, so a bare `jekyll build` also works.

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
