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
  - `stats.txt` — the same numbers as the index entry, human-readable.
    Anything never measured is written as `not recorded`.

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
