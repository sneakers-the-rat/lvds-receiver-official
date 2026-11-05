# Working notes — routing phase, expanded board (coordinator: pdlvds-route)

Clone: ~/workspace/pdlvds-route (from pdlvds-split @ db5c7ae). Parent merges/pushes; commit locally only.

## State log
- Baseline verified by own runs: pass 65 (2e43811) expanded board audit =
  69 unconnected nets / 257 total groups / 2 clearance violations (both
  justified D1 family: APD_K D1.5 vs APD_A tracks). GND 51 groups,
  +3V3D 40, +5V 27, +3V3A 13, +3V3D_CDR 10. (history/pass-0065/audit.txt)
- Tools salvage commit f15a072: bridge.py (all-pairs fix), thread.py,
  repairg2.py, hand_via.py lifted from photodiode-lvds-rx/hw.
- PASS 66 (fbc5369): GND zone outlines extended into strip
  (hw/refill_strip.py) + HV keepout notches from strip HV copper
  (hw/notch_strip.py). Audit: 69 nets, GND 51->9 groups, total groups
  257, violations 2. Intermediate refill-only state: GND 51->7,
  violations 2->10 (8 HV-vs-pour) — notch removed all 8, GND 7->9.
- repairg run exp1 (expanded->exp1): KILLED after ckpt1 audit showed
  exchange rate -1 audit group per 10 internal merges (its grouping
  is pour-blind; it was stitching GND pad clusters the pour already
  joins). Ckpt1 audit (results/audit-exp1-ckpt1.txt): 256 groups,
  GND 8, violations 2. Copper it placed is real; exp1 is the current
  working board.
- Campaign switch: bridge.py rounds (audit-visible nets, batched,
  one save per round) -> thread.py for gap>3mm/stuck pairs ->
  repairg/repairg2 mop-up; GND islands stitched last, targeted.
- 2026-11-04 ~23:06 UTC: VM REPLACED (uptime reset). KiCad + wx +
  pcbnew wiped (/usr only; workspace durable). xvfb survived.
  Recovery: first apt run wedged 26 min fetching translation lists
  (0 lists stored, partial mtimes fossilized at 20:01) — killed and
  relaunched lean (Acquire::Languages=none + timeouts): update done
  in <1 min, full install (kicad, xvfb, ngspice, gcc-arm-none-eabi)
  rc=0, pcbnew 7.0.11 verified. Java still absent -> freerouting jar
  unusable; native freerouting-cli ELF exists but crashed on this
  project's DSN in an earlier smoke test. Freerouting = optional
  side line, deprioritized.
- CI pre-check on current tree (no-KiCad steps 1,2,4,5,6,7,9):
  ALL PASS rc=0 (results/ci-precheck.log) — codec, link budget R2,
  digital sim, HV analytical, impedance, firmware host tests,
  host-tool smoke. Remaining for final: 3 (ngspice), 8 (ARM build),
  10 (ERC), 11 (DRC) — toolchain now present for all.

## State log (continued)
- PASS 67 (bf7487d): bridge campaign, 4 rounds on exp1. Groups
  253 -> 226, nets 69 -> 65, violations 2. Round yields
  -16/-6/-3/-2 (decay -> shape change). Audit quirk: GND group
  count wobbles +-3 between audits of identical bytes (hairline
  pour-polygon contacts); all other nets byte-stable. GND tail to
  be closed with real track stitches, not fill luck.
- Residue anatomy (audit-bridge-r4): rails are LONE PADS, not
  fragments: +3V3D 38 groups (U6 power pins, U5, U8...), +5V 23,
  +3V3A 9 (incl. the U6.32/33 vs C49.1 watch-item corner),
  +3V3D_CDR 7 (U4 pins). APD_K 7 lone pads (HV divider chain,
  1.0 mm rule). ~30 medium/long 2-group signal hauls (ULPI U7<->U6,
  CDR pairs to J2, CAP_* U5<->U6). -> repairg2 full sweep is the
  main line now (its per-net A* loop fans pads into the field;
  pour-blindness only wastes GND effort, harmless for rails).

- Stall rule: a cluster at 0 connections across two checkpoints ->
  ENLARGE (another strip / further spread / U6-field relief incl.
  moving connectors or APD-TIA if a proven stall requires it);
  record as a pass with dimensions. User: size is not a constraint.
- Checkpoint discipline: no run >20 min without a saved+committed
  checkpoint; commit via scripts/commit_pass.py --board <file>.
- Completion: audit 0 unconnected + justified-only clearances ->
  copy final board to hw/pdlvds_rx.kicad_pcb (make_fab.sh hardcodes
  that path) -> scripts/make_fab.sh -> verify hw/fab inventory ->
  final pass -> docs/00-status.md rewrite incl. full verification
  suite re-run (firmware host tests, codec/digital sims, ERC).
- Watch item: 18 courtyard pairs among unmoved parts incl. U6xC49/R15
  (+3V3A corner); U6-field micro-relief pre-authorized if it stalls.

## Toolchain recovery (parent directive, 2026-11-04 16:00 PST)
- PERMANENT mechanism: ~/workspace/toolchain-restore/{harvest.sh,
  restore.sh} + apt cache in workspace. After ANY VM replacement:
  run restore.sh FIRST (apt --no-download from workspace cache);
  apt network install only if it reports incomplete.
- DONE 2026-11-05 ~00:0x UTC: all toolchains verified answering
  (kicad-cli 7.0.11, wx+pcbnew 7.0.11, Xvfb, xauth, OpenJDK
  21.0.12.1, arm-none-eabi-gcc 13.2.1, ngspice). Java had arrived
  as a dependency in the apt2 wave (default-jre-headless newest).
  xvfb/xauth debs were missing from the cache (preinstalled, never
  downloaded) — fetched via apt-get download into
  /var/cache/apt/archives, then harvest.sh ran: persistent cache
  now 57 debs / 720M, all six restore-critical packages present
  (kicad, xvfb, xauth, default-jre-headless,
  openjdk-21-jre-headless, gcc-arm-none-eabi).
- repairg2 sweep (exp2->exp3, PID 31417) running since pass 67:
  still in its GND phase (pour-blind groups first, ~21-45 s per
  merge, some STILL isolated e.g. U5.9/12/15); no exp3 checkpoint
  file until the GND net loop closes. Watch: if still GND-bound
  at next poll with <15 merges, kill and switch to thread.py
  chains under checkpoint-per-invocation discipline.
