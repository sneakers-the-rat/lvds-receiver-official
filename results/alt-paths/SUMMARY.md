# Routing alt-paths — SUMMARY for the completion coordinator

Branch `routing-alt-paths` (not pushed). Everything below was measured
with the repo's own tools on files in this branch. Base: pass-10 board
`hw/pdlvds_rx.movedr.ckpt1.kicad_pcb` at commit `d489c78`, extracted to
`results/alt-paths/work/pass10.kicad_pcb` (md5
`205f576b815cbc0655c2cee8cb3548e1`); its placement-only form (tracks and
vias stripped) is `results/alt-paths/work/pass10-placement.kicad_pcb`.

## 1) ADOPT FIRST — Path A placement-relief candidate

**Take this file:** `results/alt-paths/placement-candidate.kicad_pcb`
(placement only, unrouted — route it exactly as pass 9's placement
revision was routed). It is the pass-10 placement with **25 footprints
moved, nothing else changed**: same outline (100×80 mm), same 144
footprints / 681 pads, no rotation or side changes, connectors and the
APD/TIA analog cluster (D1, U1, R1, C1) unmoved. Move list with
per-part rationale: `results/alt-paths/apply_moves.py` (the MOVES
table) — the script reproduces the candidate from the pass-10
placement in one run.

### Metrics (before → after)

| Metric | Before (pass-10 placement) | After (candidate) |
|---|---|---|
| Boxed pads (definition below) | **17** of 392 | **10** of 392 |
| Courtyard overlaps, polygon-exact | **32 pairs** | **2 pairs** |
| Courtyard overlaps, bbox | 33 pairs | 2 pairs |

Pad-by-pad diff over all 392 classified pads: **zero regressions**
(no pad that was open became boxed); 7 pads unsealed: U5.16 (+3V3D),
U14.1 (+5V), U13.10 (+VA), U5.6 (CDR_CLKP), U10.9 (HV_SHDN),
R40.1 (SET_P), R12.1 (THRADJ).

**Boxed-pad metric, precisely:** `results/alt-paths/classify_boxed.py`
— for every pad of every non-GND multi-pad net, the pad's first-move
fanout under router6's exact shape-distance clearance model (the
verbatim `fanout_targets()` construction from `hw/diagnose_groups.py`);
BOXED := fanout == 0 AND bounded reach from the pad's cells ≤
n_pad_cells + 4 (the NO_EXIT test of `hw/diagnose_groups.py`). Same
script, unchanged, run on both boards:
`work/boxed-before.txt`, `work/boxed-after.txt`.

**Courtyard metric, precisely:** `results/alt-paths/courtyard_audit.py`
— two footprints collide when they are on the same side and the
intersection area of their courtyard polygons (F.CrtYd / B.CrtYd) is
> 0.001 mm² (SHAPE_POLY_SET boolean intersection). The bbox count (33)
reproduces the parent's quick measurement exactly; polygon-exact is 32
(U6×R16 is bbox-only). 5 footprints have no courtyard polygon (D1, U9,
SH1, D2, T1) and are invisible to this metric. Results:
`work/courtyard-before.txt`, `work/courtyard-after.txt`.

### The 10 pads still boxed are NOT placement problems — do not chase them with placement

Each was probed individually (`work/probe-<pad>.txt`, exact router
items + clearance demands; `work/probe_pad.py`):

- **D1.2 / D1.4 / D1.6 (APD_A) and D1.5 (APD_K)** — sealed inside D1's
  own footprint: APD_K is an HV-class net (clearance demand 1.00 mm);
  D1's anode pads sit 1.05 mm (surface) from the cathode pad, so every
  legal first step needs 1.125 mm and gets at most 1.075 mm. Moving or
  rotating D1 moves both pads together — the seal is invariant. This
  is the same same-footprint situation `hw/check_pcb.py` already
  waives as "intrinsic" pairs; the router model has no such waiver.
  Fix belongs in the router/model (e.g. waive same-footprint pairs in
  `seg_margin`), not in placement.
- **U9.1 (I2C_SCL) / U9.3 (TMP_ALERT) / U9.5 (+3V3A) / U9.6 (I2C_SDA)**
  — sealed by U9's own exposed pad: every outer pad centre is
  0.075 mm from the GND exposed-pad rect, and each pad is in line with
  a neighbour pad; the model's first-step needs 0.30–0.35 mm. The
  footprint is symmetric, so rotation does not help; moving U9 moves
  the seal with it. Footprint/model issue, not placement.
- **J2.5 (CDR_CLKP) / J2.6 (CDR_CLKN)** — J2 is the edge clock
  connector; pads 5/6 sit at x = 102.08 mm, outside the board outline
  and > 1.5 mm beyond the router grid edge, so no fanout bend can land
  on-grid; their grid-clamped proxy cell falls inside J2.3's GND pad.
  A model/edge artefact of an edge-launch connector, not placement.

So: of the original 17, the 7 that placement could fix are fixed; the
other 10 need a model decision (same-footprint waiver) or are
connector/grid artefacts. If the coordinator applies a same-footprint
waiver in the router, re-run `classify_boxed.py` — expect D1×4 and
U9×4 to open; J2×2 will not.

### What the moves were (summary; full rationale in apply_moves.py)

- Unsealing moves: **C28** (its GND pad physically overlapped U5.6,
  probe distance 0.000), **C17** (0.080 mm from U5.16), **R12** (its GND
  pad overlapped U13.10, 0.025 mm; R12.1 was itself boxed against
  U13's exposed pad), **C14** (0.226 mm from U14.1), **R40** (C41.2
  overlapped its west edge), plus **R27** shifting 0.75 mm SE, which
  also released U10.9.
- Courtyard-only relief: C4, C33, C38, D4, C5, C20, C21, C22, R24,
  R17, C37, R42, R5, R11, C51, and the x=89 column (C49, C19, R15,
  R16) shifted 0.5 mm east out of U6's courtyard edge.
- Remaining 2 courtyard pairs are both in the analog front-end cluster
  and were left deliberately: **U1×R1** (0.17 mm²; R1 is the TIA
  feedback resistor and must stay tight to U1) and **D8×U1**
  (0.79 mm²; BIST diode against the TIA, pads clear, no seal).
- **Bottom side considered and rejected:** all 144 footprints are on
  top and every fixable seal yielded to a small top-side move, so no
  part needed flipping. Flipping decoupling caps to B.Cu would consume
  L2 routing area under their ICs and force two-sided assembly;
  the empty bottom is worth more as routing space. Nothing in this
  candidate depends on that choice — a future pass can revisit it.

## 2) Path B — Freerouting v2.5.0 baseline

**Status: RUNNING, verifiably.** Current run, as of 2026-11-04
12:45 UTC:

- Process: **PID 19062** —
  `/usr/lib/jvm/java-25-openjdk-amd64/bin/java -jar
  ~/workspace/tools/freerouting/freerouting-2.5.0.jar
  -de pass10.dsn -do pass10.ses -mp 20`
  (launched detached via `work/run_freerouting2.sh`, setsid; this is
  distinct from the coordinator's own Freerouting process PID 14778,
  which is routing a different DSN in the main clone).
- Log: `work/freerouting-jar2.log` (growing; 43 lines at 12:45 UTC),
  heartbeat `work/fr2-heartbeat.log` (one timestamped line/minute
  with the live jar-log line count), final status will land in
  `work/freerouting-run2.status`.
- Progress in the log: fanout stage completed 12:44:05 UTC —
  342/503 SMD pins escaped (68.0%); **auto-routing stage started
  12:44:10 UTC with 135 unrouted items**, baseline score 551.57.
  SES is written only at the end; none exists yet.

**Correction to this file's earlier state (the 04:39 watchdog flag
was right):** the first relaunch attempt (12:37 UTC) died within
seconds — a shell operator-precedence bug in the launch command ran
java in the wrong working directory and it aborted with "Couldn't
read the input file 'pass10.dsn'" — while its detached heartbeat
loop kept writing "alive" lines until 12:39 UTC with no process
behind them. That shell and heartbeat were killed, the failure is
preserved in `work/freerouting-jar2.log` (12:37 entries), and the
current run is the wrapper-script relaunch described above. The
pre-compaction first attempt (Java 25, reached fanout pass #2) was
killed by an environment reset that also removed the KiCad/Java
installs; log at `work/freerouting-jar.log`.

Established so far, with evidence in `work/`:

- The official native CLI (`freerouting-cli` 2.5.0, sha256 verified
  against the release checksums file) **cannot run here**: it loads
  the DSN, reports the same 439 pre-existing clearance violations,
  then dies with a GraalVM `UnsupportedFeatureError:
  SerializationConstructorAccessor class not found for ...
  ComponentOutline`. Log: `work/freerouting-smoke.log`.
- The official jar (same release) under OpenJDK 25.0.4.1 loads the
  DSN (`work/pass10.dsn`, produced by `hw/make_dsn.py`: 113 nets;
  F.Cu/B.Cu GND planes removed, In1.Cu kept as the solid GND layer)
  and routes — see the live run above.
  Jar sha256 `f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7`
  — note the release checksums file covers only the CLI archives, so
  the jar itself has no upstream checksum to verify against; its
  manifest matches the release (Build-Date 2026-10-05, revision
  `b647a2f824cfbc54bc4dcaee71b03b7cd945eb76`). Install record:
  `~/workspace/tools/freerouting/PROVENANCE.md`.
- When the SES lands: import with `hw/import_ses.py` onto the pass-10
  board, audit with `hw/check_pcb.py`, verdict recorded here.

## Files in this deliverable

- `placement-candidate.kicad_pcb` — Path A candidate (adopt this).
- `apply_moves.py`, `classify_boxed.py`, `courtyard_audit.py` — the
  tools; rerunning them on any board reproduces every number above.
- `work/` — before/after audits (`boxed-*.txt`, `courtyard-*.txt`),
  geometry dumps (`geom-before.txt`, `geom-after.txt`), per-pad seal
  probes (`probe-*.txt`), per-net pocket diagnostics (`pocket/*.txt`),
  pass-10 board + placement + DSN, Freerouting logs.
