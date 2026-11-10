# DISTRICT STATUS — ba session handover (successor to az's map)

Frontier after ba: **exp254 / pass 217** (banked via commit_pass; verify
HEAD on origin before trusting). Board state at exp254:
- KiCad DRC: **4 violations, all standing J1 copper_edge_clearance**.
  Unconnected items: **2 — XI and USB_RST**.
- check_pcb: nets 2 {XI, USB_RST}; census/courtyard/blind: see
  `check254_out.txt` beside this file (delta vs exp253's 120/0/SH1-21
  recorded in the pass-217 commit).

## What ba banked

**Pass 216 (exp253, origin ecd4375)** — PHY_1V8 CONNECTED via the user's
C22-north relocation. C22 (72.5,18.0) rot0 → **(77.17,9.95) rot90**;
pads PHY_1V8 (77.17,10.43) N / GND (77.17,9.47) S. PHY hop: one F seg
(77.17,10.43)→(77.90,10.08) into PHY's via. GND tie: F stub
(77.17,9.47)→(76.975,9.6) + new GND via d0.5 at (76.975,9.6).
ULPI_STP southern half re-laid ("STP7", design_stp_south7.json):
transition via (76.445,9.03), In2 diagonal to (77.2,5.9), B/F hops
rejoining the kept approach at the (74.90,−1.30) T-join. C22 SE site
family evaluated and REJECTED with arithmetic (t_ba19): all six sites'
PHY pads fenced −0.47…−0.65 by CDR_SQUELCH/+3V3D F webs; SE also fails
the user's pay-for-itself test. DRC 5→4, check_pcb nets 3→2, census
109→120 (+11 all C22.1×XO staircase adjacency 0.205–0.21, DRC-legal).

**Pass 217 (exp254)** — district prep, two proven moves:
1. **1V8A notch journey re-laid compactly** (the user's "loopy journey
   climbing to the notch via"): via (75.27,10.33) → **(75.45,10.6)**
   d0.5; F stub single seg (75.72,11.0)→(75.45,10.6); B head
   (75.45,10.6)→(75.0,11.5)→(74.45,12.1)→(73.50,12.55). Model gates:
   segs worst +0.006, via worst +0.017 (both vs +3V3A, model-circle
   conservative). 1V8A frags 1.
2. **STP western B excursion removed — WITH A HARD LESSON.** The
   excursion (76 B segs, centres x[74.3,76.0] y[13.4,17.2]) had two
   boundary joins ((75.95,13.6),(75.95,16.6) in the model) and I read
   that as a redundant loop. **WRONG**: t_ba48's model fragments went
   3→4 after the rip (frag B split) and I misreported it as preserved.
   On the board the excursion WAS the through-path between the legs
   chain (ends (76.05,16.7)) and the descent head (76.05,13.45): the
   rip also ate two column segs whose centres sit at exactly x=76.0.
   DRC caught it (STP split + 2 dangling). **Test for "redundant":
   fragments before == after INCLUDING terminal sets — boundary-join
   counting is NOT sufficient.** The real connection was re-made
   deliberately and compactly (cleanup doctrine): one B chain
   (76.05,16.7)→(76.35,15.6)→(76.35,13.9)→(76.05,13.45), bowed east
   around the **GND EP-stitch via (75.6,14.75) d0.6** (clearance
   0.05 if run straight at x76.05 — DRC caught that too; the bow
   gives +0.35). Net yield: ~11 mm of loopy B copper deleted, STP
   still connected, both referees clean. The freed corridor
   x[74.3,76.0] y[13.4,17.2] on B is now EMPTY except the new chain
   at its east edge.

## XI — the full fence map (exp254 configuration; NOT connected)

Terminals: arc via (75.625,18.625) r0.3 / C20.1 (75.72,18.73) vs
U7.28 pad rect x[76.125,76.375] y[11.12,12.0]. The drop is sealed at
BOTH ends and in the middle; every fence below is measured, not
guessed (t_ba47–t_ba56):

**Start seal (via wall)**: DIR via (75.5,17.52), STP dive via
(76.065,17.96), CK via (76.625,17.5) — centre spacings 0.565/0.56; a
track needs 0.55 from EACH via centre → southward exit on F or B is
arithmetically impossible between them. East of CK: PHY's B chain
diagonal (76.95,14.99)→(77.80,16.20) + PHY via (78.10,17.50) seal it.
West of DIR: DIR's own B track (centre (73.44,18.32)) + 1V8A head
chain seal the B west channel's south exit; the channel itself
(x[74.6,75.95], y[12.6,18.6] B) is EMPTY except DIR's via — but its
south exit crosses the 1V8A B head chain (75.27,10.33)→(73.50,12.55)
diagonal wall. Also: **the item-model A\* cannot start at the arc
via** (returns NONE for any goal; mid-corridor starts work — test A
in t_ba52). Hand legs from the arc are required whatever the design.

**Middle walls**: CK's In2 cross {vertical x74.62 y[6.38,13.5],
horizontal y13.5 x[74.62,76.62], vertical x76.62 y[13.5,17.5]} is a
complete In2 wall around the SW quadrant (crossings: x74.62 only at
y<6.38 or y>13.5-with-horizontal-clearance; y13.5 only outside
x[74.62,76.62]). +3V3A's In2 diagonal (75.50,9.00)→(76.62,10.25)
fences In2 rises into the pocket from the south-west.

**End seal (the pocket)**: U7.28 admits ONLY an F leg from the south
into its south edge (pad-row gaps are 0.25 — no track, no via in the
band y[11.12,12.45]). The final via must sit at y≤~10.67 south of the
pad row, and its F leg runs north at x≈76.2. Four discs fence every
candidate site: XO's F west run (y≈9.63, x72–76.2), 1V8A's notch
stub/via (now at (75.45,10.6) after pass 217 — the pocket's west
fence MOVED EAST and its stub diagonal is gone), XO's staircase
(foot (76.20,9.90) climbing to vertical x76.55 y[10.25,11.53]),
STP7's B descent at x76.2 (y9.3–13.5). Best grid optimum with ALL
fences standing (descent hypothetically at x76.48, foot jogged):
**−0.076** (binding: 1V8A notch via, old position). Descent cannot
move east (PHY B chain corner (76.95,13.02) −0.03; C22 GND via
(76.975,9.6) −0.038) nor west (it would eat the pocket). XO's run
cannot move south (GND stitch vias (72.9,9.45),(73.53,9.5) + +3V3A
via (75.62,8.62) r0.4: y9.3 run −0.4/−0.075) nor to B (crosses
+3V3A's B diagonal (75.62,8.62)→(71.25,11.12)) nor In2 (CK vertical).
XO foot jog (rip 13 F segs centres x[75.85,76.52] y[9.6,10.28], lay
(75.90,9.70)→(76.28,10.0)→(76.52,10.22)) gates −0.01 vs C22.1 in the
model = +0.07 rect-truth — usable as part of a combination.

**What the successor should try, in order:**
1. Re-run the pocket-via grid optimisation on exp254 (notch v2
   moved the west fence: via (75.45,10.6), stub is now the single
   seg (75.72,11.0)→(75.45,10.6)). My hand calc says the lens
   around (75.85–75.95, 10.3–10.42) improves by ~+0.05 on the
   1V8A fence but the B-side descent fence (x76.2, via needs
   x≤75.65) still contradicts the F-side staircase-foot fence
   (needs x≥~75.85). If the grid still returns negative, the
   pocket needs the descent's southern span re-laid: STP7's
   descent could dive to In2 at (76.2,11.0) IF the +3V3A In2
   diagonal is itself jogged south at its east end — untested.
2. The five-net mega-relay (t_ba56) is HALF-PROVEN: notch v2 ✓
   (banked in 217), STP In2 underpass ✗ (dies on BIST_DRV's In2
   web at y5.5, x74–76.5 — items (74.25,5.75),(74.5,5.5),(74.0,6.0)
   + CK In2 (75.12,5.88); find BIST_DRV's channel or route the
   underpass at y6.8–7.5), DIR via west ✗ (dies on ULPI_NXT's F
   escape + U7.11 pad −0.3; DIR's full F/B topology was never
   dumped — dump before designing), CK via east move (77.0,17.3)
   is the untried wall-breaker (opens a 1.19 gap dive↔CK; CK's F
   stub grazes U7.15's pad rect ~0.3 — re-lay stub via
   (76.85,16.9)).
3. USB_RST (untouched by ba): U7.9 (74.25,16.4375) vs U6.40
   (74.75,4.662). ay's both-boxes shape: dive (74.125,16.375),
   ride x74.125, via (74.125,6.0), arrive U6.40; DM_PHY F loop is
   the coupled re-lay partner. The freed B corridor (excursion
   grave) and the notch v2 geometry change the north box — re-gate
   ay's shape on exp254 before building.

## Campaign traps relearned this session (do not repeat)

- **item_margin pad sentinel**: pads as SUBJECTS return 9.9 —
  gate pads as OBSTACLES only. (Cost ba its first C22 build.)
- **Model pad margins use circumscribed circles** (~0.1–0.18
  conservative vs KiCad's rect truth): a small negative vs a PAD
  may be DRC-legal — verify with rect arithmetic, never bank on it
  blind.
- **Centre-rule rip boxes eat kept branches** at box edges (pass
  216's dangling class; pass 217's x=76.0 column segs). After any
  rip, DRC-check for dangling BEFORE banking; assert victim counts
  per net on the board.
- **"Loop" ≠ redundant**: prove by fragments-before/after with
  terminal sets. See pass 217 lesson above.
- **Via GetLayer() in board dumps returns F_Cu for through vias** —
  layer-filtered via censuses silently drop them (t_ba63 missed
  the GND stitch via (75.6,14.75) this way; DRC caught the graze).
- **ZONE_FILLER**: use `pcbnew.ZONE_FILLER(b).Fill(b.Zones())`
  verbatim — a filtered Python list of zones raises a SWIG
  TypeError in this build.
- Xvfb :99 dies with VM replacements; restart it manually
  (`Xvfb :99 -screen 0 1024x768x24 &`), `xvfb-run` is flaky.
- pcbnew coords in this harness are RAW (no y-flip); footprint
  rotation: SetOrientationDegrees(90) puts C22's PHY pad NORTH.

## Named cleanup candidates (not defects)

- +3V3A B diagonal shortcut (68.88,12.38)→(68.38,17.5) paralleling
  its L-rail (x68.62 vertical + y8.62 base) — redundancy unproven;
  test by fragments before touching.
- STP7's kept southern approach west of the (74.90,−1.30) T-join
  parallels the new southern route — fragment-proof before ripping.
- The NW loopy-rail sighting = +3V3A's B L-rail (t_ba20 census in
  the ba evidence); dense micro-seg fields nearby (CAP_DATA In2
  487, CAP_CLK B 239) are single A* journeys, NOT redundancies.

## SH1 blind spot (standing, named per orders)

check_pcb courtyard blind list remains SH1-only (21 fallback pairs);
SH1 has no drawn courtyard — needs the semantic covering-part
answer (S1001 clip conversion from F-13 still pending). The 2 D1
clearance lines remain standing, untouched, per docs/07 (condition
(a) land-pattern proof still unverified).
