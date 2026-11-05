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

## THE GRID FIX (2026-11-05 ~01:5x UTC) — read this first
- Passes 65-71 routed with a BROKEN search grid: hw/router.py was
  still sized for the pre-expansion board (W,H = 400,320 =
  100x80 mm; cell_of clamped y to [0,80]). Every strip item
  (y<0) crushed onto grid row 0: strip searches tested phantom
  geometry along the field's north edge, failed at 0 s, or
  emitted vias at y 0.6-2.1 (30 APD_K-vs-pour violations at
  pass 71). The audit (check_pcb, exact shapes, no grid) was
  never wrong — which is why merges that DID land were real.
- Fix (tools commit d4a9e0d): grid 400x440, OY=-30 in router.py;
  cell_of + all 8 cell->mm conversions in router.py/router6.py
  offset by OY; repair.py/diagnose_groups.py inherit via imports.
- Smoke proof: CDR_LOS/CDR_LOL/CAP_CLK — 0 s failures in every
  prior run — connected in 16/23/52 s on an exp7 copy, audit
  59 -> 56 nets, no new violations.
- Toolchain: VM replaced again ~01:31 UTC; restore.sh recovered
  EVERYTHING from the workspace apt cache in <55 s (incl. a
  freerouting jar smoke test pass — Java + jar now work).
  ngspice is NOT in the restore set (needed only for final CI
  step 3; fetch or extend the cache before the final pass).
- heal-all2 (exp7 -> exp8, fixed grid) running from ~01:5x UTC.
  Remaining knowns after it: 16 no-stub pads for hand_via
  (U9.5, U7.4/6/7, U14.6, D1.5, J1.B5, U10.7/8/9, U13.7,
  U6.26/29/40/70/74), re-notch for APD_K-vs-pour (one via at
  (13.6,30.6) is outside notch_strip's y<5 filter — check its
  state on the exp8 audit), GND's 4 audit groups (targeted
  stitches), then the residue loop to 0.

## FAILURE-CLASS QUEUE (2026-11-05, parent method change — replaces count-chasing)

Rules: each class = mechanism statement -> targeted fix (tool or board)
-> regression test in the SAME commit -> closed with evidence. No
undirected sweeps: heal/ripup/bridge/thread runs execute only against a
named class with a stated hypothesis; a run connecting 0 against its
class closes the hypothesis and the next move is a new diagnosis. The
word "justified" is retired; audit exceptions exist only as a registry
inside hw/check_pcb.py with an evidence citation per entry (the
registry mechanism lands with the first exception that passes an
evidence gate). Retroactive regression tests LANDED (commit a62a013):
hw/tests/test_router_grid.py (grid/OY, pre-d4a9e0d FAIL / now PASS),
hw/tests/test_hand_stub.py (stub-on-pad, pre-feceb01 FAIL / now PASS);
outputs in results/test-regressions.txt.

Residue basis: pass 76 audit (28 unconnected nets, 17 violations).

### CLASS T — thread via-rip execution gap (tool defect; NEW at pass 76) — FIXED, board repair pending
Mechanism: thread.py's rip reconstruction re-tests only same-layer path
SEGMENTS against live tracks. Blocker tracks that via_blockers() priced
as ripped during the search are never removed, so thread_far's placed
vias violate their own priced victims. Evidence: 15 of pass 76's 17
violations (SLICEP via@(51.5,-17.5) vs SLICEN/CDR_NIN x8, HV cluster
threads x7). Diagnosis addendum (coordinator #4, exp13-vs-exp12 track
diff): TWO sub-defects — (T1) priced rips executed by a capped
count-heuristic over segment collisions only, so via-disc-priced
victims were never removed and segment victims were removed by
count, not identity; (T2) the anchor stubs (facing point <-> first/
last lattice node) were placed with NO blocker test at all — the
MOS_G-vs-HV_GATE and HV_RT-vs-HV_SS violations are both stub tracks
(their start points match stub geometry exactly).
FIX (thread.py + thread_far.py, same commit as the regression
test): the search prices the anchor stubs like any other segment —
start = the four lattice corners around the facing point, each
initialised with its stub's rip set (a walled stub discards that
corner); a goal node is accepted only if its goal stub is rippable,
its blockers joining the rip set. The reconstruction executes
EXACTLY the priced set: rip_targets() resolves each priced item
index to its live board object via the build_items/GetTracks()
correspondence, VERIFIED per item (net + shape BBox) — any mismatch
aborts the thread with nothing placed. Regression:
hw/tests/test_thread_via_rip.py (a wall pad forces a layer change;
the victim is a wide In1_Cu bar only a via disc can price). Clean
evidence in results/test-regressions.txt: fixed tree PASS (both
tools rip exactly the victim, audit-clean); pre-fix tree FAIL
(both rip 0, victim survives, placed via violates it).
TOOLING TRAP found en route: every hw module self-inserts the
RELATIVE path 'hw' into sys.path at import, so in a multi-tool
test the second tool imported resolves against the CWD's tree, not
HW_DIR — a first pre-fix capture silently tested the fixed
thread_far and was discarded. Tests must load tools by explicit
path (test_thread_via_rip.py does) or run where 'hw' resolves to
the intended tree.
BOARD REPAIR (in progress): the full 7-net redo on exp12 was run
TWICE with identical results (process records + on-disk log agree;
an interim snapshot claiming all 7 threaded + saved was NOT borne
out by either and is discarded). Honest per-net outcomes with the
fixed tool: CDR_VREF threaded (rips 2, executed exactly),
REFCLKN threaded (rips 2), SLICEP threaded (rips 6 — the priced
CDR_NIN/SLICEN victims pass 76 left standing are really removed;
their repayment is Class B growth). HV_SS: NO THREAD at honest
prices (pass 76's "thread" existed only via unexecuted rips).
HV_GATE: ANCHOR STUB WALLED AT START — all four start corners'
stubs hit walls (pass 76 placed that stub untested; it grazed
R27.2). Both failure modes are the U10 locality's business:
they move to Class A / the U10 placement work, where moving the
blockers is the lever. HV_INTVCC: search exceeded the 1500 s
run budget in this field both times (slow, NOT proven
impossible) — to be attempted solo. The redo was therefore
split: pass 77 = exp12 + [CDR_VREF, REFCLKN, SLICEP, +5V] with
the fixed tool; HV_INTVCC solo and the U10 locality follow.
Status: MECHANISM CLOSED; board repair partial by the tool's own
honest refusals — the refusals ARE the class evidence.

### CLASS A — NO_EXIT pads (local surgery per pad; blocker named)
Pads sealed in their first millimetre (diagnose reach=1 on exp12;
lone-pad groups in the pass-76 audit). Routing effort and board area
are irrelevant to this class. Fix per pad: move/rip the specific
blocking item named by probe-via, or escape on the one free
layer/direction; stub/via verified by audit after each. Members
(blocker where probed): U9.5/+3V3A (neck blocked by GND pad U9.7; via
disc clears), U7.6/+3V3A, U7.4/+5V, U14.6/+5V, U7.7/DP_PHY,
U10.7/HV_GATE (via disc blocked by one +5V track — threaded at pass 76
but its net still has 2 groups), U10.8/HV_INTVCC (threaded at 76),
U10.9/HV_SHDN, U4.12/+3V3D_CDR (NEW: split off by a thread rip at 76),
U13.7/SET_P, U6.29/ULPI_NXT, U6.40/USB_RST, U6.70/ULPI_D4,
U6.74/ULPI_D6 (NRST bundle across its pin tips), U9.1/I2C_SCL,
U9.6/I2C_SDA, U9.3/TMP_ALERT, C22.1/PHY_1V8, C15.2/CF2,
U5.3/CAP_DATA, U4.27/CDR_SQUELCH, J1.B5/CC2 (disc blocked by VBUS_RAW),
D1.5/APD_K (same-footprint geometry; its connection is owed as routing
— see the standing D1 audit lines below). Membership is confirmed per
pad by probe/diagnosis as surgery reaches it. Status: OPEN (0 closed).
Corroboration (FR verdict, 2026-11-04 ~21:35 PST): Freerouting's
fanout failed on the same pin population (355/503 escaped) — the
seals are geometry, not search effort.
STUB-WALL DIAGNOSIS on exp14 (results/probe-stub-walls-exp14.txt;
the fixed thread's own blocker math at both anchors of the
nearest pair): HV_GATE is walled at BOTH ends on F — start (R27.1
group track, facing (15.562,-18.518)): all 4 corners blocked by
the MOS_G pad R27.2; goal (U10.7, facing (15.425,-14.650)): all
4 corners blocked by pads U10.8 (HV_INTVCC) and U10.11 (GND EP).
HV_SS: start (C30.1) CLEAR at all corners; goal (U10.3, facing
(12.575,-14.850)) walled at all corners by pads U10.4 (HV_RT)
and U10.11 (GND EP). +5V's nearest pair (U11.12 <-> its track,
gap 0.20): start walled by a GND pad at all corners; goal has
clear corners. Pattern for the whole U10 row: the facing points
thread chooses face WEST, into the package's own pad fence
(EP + adjacent pads); the pads' open side is EAST. Surgery
direction for the U10 locality: hand-placed east-side escape
stubs on U10.3/U10.7/U10.8/U10.9 (audit-verified per stub) to
move the thread anchors to the open side, and an escape via/
extension on the R27.1 group's track west end for HV_GATE's
start. These are placement/surgery passes, not search retries.
HOLD (parent order, 2026-11-04 ~21:12 PST): all U9 members (U9.5,
U9.1, U9.6, U9.3) are OUT of this class until the re-sync wave — the
parts audit (docs/08-parts-lock.md, main d7acb61; 115 LOCKED / 29 NOT
LOCKED) measured U9's footprint defective by construction: all six
signal pads overlap the grounded exposed pad by 0.20 mm (pins short
to GND on copper) and the geometry disagrees with TI's DRV0006B
callouts. U9.5's reach=1 "seal" was partly the broken footprint, not
a routing problem. The pad layout WILL be redrawn; no routing effort
on U9's current pads. U10 locality and Class T proceed as planned.

### CLASS B — two-island long hauls (negotiated rip-up territory)
Both endpoints reach open field (diagnose reach 400k+); the floods do
not meet through the occupied middle at acceptable cost. Proven tool
limit: heal's astar6 refuses this residue at expansion cap 1.5M AND at
15M (heal_big probe, CDR_VREF, 162 s, 0 connected) while the
diagnostic BFS reaches the goal halo — the grid A* cost model, not
the geometry. Members: ULPI x8 (D1-D6, NXT, STP) + USB_RST + DP_PHY
(U7 legs), CDR chain (CDR_PIN, CDR_SQUELCH, CAP_DATA), APD_K chain
(D1.5 leg, RJ2.2 leg), I2C_SCL/SDA + TMP_ALERT hauls, CC2, CF2,
HV_SHDN haul, SET_P haul. FREEROUTING VERDICT (parent, 2026-11-04
~21:35 PST): LOSES — no board produced. Branch fr-attempt in
pdlvds-fr2, final commit 67cc2f6 (RUN-NOTES.md + freerouting.log
are the record). Full 90-min budget after a VM-replacement
restart: fanout escaped only 355/503 pins; auto-routing unrouted
went 125 -> 120 -> 147 -> 146 -> 147 (worse after pass 1,
pinned); no SES written at the timeout. CLASS B IS THIS LANE'S
NOW: the authorized fallback applies — thread/thread_far per
pair (Class T fixed), and endpoint geometry where diagnosis
indicts it: a local respread of U6's decoupling/pin-escape web
(U6 never moved in the expansion) is authorized under the
standing enlargement directive if diagnosis indicts the U6-side
exits. Status: OPEN (this lane; FR lane closed).

### CLASS R — rail islands (short/medium hops; thread-class vehicle)
+5V (6 groups), +3V3A (3), +3V3D_CDR (3), PHY_1V8 (3), PHY_1V8A (2),
HV_RT (2 — split by a thread rip at pass 76; the two groups' tracks
already overlap in x at y~-14.4), HV_GATE remainder (2). Vehicle:
thread/thread_far per pair AFTER Class T is fixed (its via bug is
exactly what bit the HV cluster), or hand hops where the gap is
sub-millimetre. Thread-victim splits (HV_RT, U4.12, +5V's growth)
are repaid inside this class's fixes. Status: OPEN.

### Queued placement pass — board re-sync wave (parent updates, 2026-11-04 ~21:01 + ~21:12 PST)
When the HV-fix and parts-fix schematic changes land on main, the
parent hands this lane the merged tree and it is absorbed as ONE
placement pass BEFORE the class queue resumes: place/replace in
the HV and north areas, rip only the copper the footprint changes
invalidate, re-audit. Known contents of the wave:
- HV interlock jumper header J5 (FINAL data, parent 2026-11-04
  ~21:14 PST): footprint Connector_PinHeader_2.54mm:
  PinHeader_1x02_P2.54mm_Vertical; pin 1 = HV_EN (from PC7),
  pin 2 = HV_SHDN. Place at the board edge near the HV cluster.
  The sense is PA6 on HV_SHDN, already in the netlist — no
  separate sense net to route beyond HV_SHDN itself.
- U9 footprint REDRAWN (current pads defective — see the Class A
  hold above); U9 locality work resumes only on the new pads.
- D4 SMA -> SMB; C4 0603 -> 1206; HV resistor series strings;
  a specified flyback transformer footprint.
Not actionable until the merged tree is handed over.

### D1 owner decision (parent update, 2026-11-04 ~20:53 PST) — FIX LANDED 57a1150, gate (b) PASS / (a) OPEN
Owner directed the D1 fix: a hardware population clamp on the HV
set-point network. LANDED on main at 57a1150 (verified in this
clone by fetch + primary records, 2026-11-04 ~21:14 PST):
results/hv_clamp_a.csv at that commit shows V_HV = 253.17 V at
DAC = 0 (the maximum), inside the C30737's 260 V VBR rating —
docs/07 condition (b) PASSES, the fry path is closed in the
schematic. Condition (a) land pattern remains UNVERIFIED, so
the 2 APD audit lines stay as violations exactly as written
(standing-lines section below) until (a) closes. The same merge
carries the J5 interlock: CONNECTIONS.md@57a1150 — PC7 = HV_EN
reaches the SHDN node only through the J5 jumper (J5.1 = HV_EN,
J5.2 = HV_SHDN); PA6 = HV_SHDN analogue sense; SHDN divider
R25 143k/R26 33k; jumper absent = the converter cannot start
under any firmware state.

### Standing audit lines (not a class, not work items)
The 2 APD_K-vs-APD_A clearance lines (D1.5's own terminal pair) stand
as violations as written. The directed exemption STOPPED at its
evidence gate: docs/07-d1-terminal-pair-evidence.md (datasheet VBR
max 260 V < design maximum bias 420 V). They leave only via an owner
decision (a hardware bound on the D1 rail inside the part's envelope,
or a detector rated for the design bias). No registry entry exists.
