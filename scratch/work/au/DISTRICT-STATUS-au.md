# CAP district — au-session status (2026-11-08, in progress)

## Baseline
exp240 / pass 209, origin 539a22c. DRC 7 unconnected, 4 violations
(J1 copper_edge). check_pcb 7 nets, census 109, courtyard 0, SH1 21.

## Pair synthesis — SOLVED in the item model (t_au1–t_au13)
CLK takes a B-layer corridor ride; DATA keeps the In2 west ride.
The shared-corridor competition (pair deficit 0.046) is gone because
the two nets no longer share a layer plan.

### CLK (SETTLED, exact-legal)
- Head (from t_au2 A*, PG braid ablated): esc via (70.02,1.83) ->
  B ride to (64.75,16.95) -> In2. Exact vs full pool (t_au6): clean
  except the arrivals below.
- Arrival (t_au9, needs XO In2 box ablation + P3F ablation):
  In2 (64.75,16.95) -> via (70.1,21.8) -> F -> via (73.25,21.75) ->
  In2 -> via (74.4,22.9) -> F -> U5.5 pad (76.525,25.385).
  Exact worst +0.000 (via (74.4,22.9) vs CDR_DATN F seg — the known
  knife-edge family). Journey: journey_au9_CLK.json.
- CLK conflicts ONLY with: PG B braid (corridor), +3V3D F web at U5,
  XO In2 web (arrival box). All three are re-lay items (below).

### DATA (route settled except the pocket entry)
- DATA30 journey (In2 west ride + F hop (63.55,11.95)/(64.7,15.45)
  + NE ride + arrival vias (72.6,19.3),(74.9,22.3)) is exact-legal
  vs the full pool EXCEPT: entry swing vs HV band (rides the band
  line, -0.425) and NE ride vs XO web (ablated by design). Its entry
  must be re-planned; the rest stands.
- Entry is SEALED in the current pocket configuration: fine-grid
  (0.025) 3-layer A* fails; single/pair ablations of THR66 via,
  GND67 via, SCL diagonal, +3V3A via all fail (t_au13/13b). NW gates
  bind vs +3V3A via (69.125,4.375) r0.4, SCL diagonal, GND via/seg;
  F west gate sealed by EP-corner/GND-via disc overlap (0.687
  centres vs 0.9 radii sum); south swing dead (band); B west dead
  (PG vertical x68.625, not ablated).
- Widest in settled model: -0.070 base; every single fence ablation
  caps at -0.025 (t_au10/10b/11) — distributed, no single keystone
  EXCEPT the one the at-session already named: SDA via (69.32,2.14)
  blocks the SCL chord, and the SDA via is trapped by U9's pads.

## THE MOVE: U9 WEST 1.0 (pocket rebuild)
U9 centre (68.25,2.75) -> (67.25,2.75). Proven geometry (t_at21,
re-gate on current board): SCL via (69.35,1.40) r0.25, chord bend
(68.8,1.9) [slot slack +0.320 vs band], SDA via (69.4,2.2) r0.25.
DATA then enters through the band<->chord slot (0.80 wide vs 0.60
needed) and rides SW of the SCL chain to its west ride — it never
crosses the SCL chain (verified against DATA30's line). CLK on B
is unaffected (U9 pads are F-only). v7's self-seal was a property
of the OLD pair configuration (CLK on In2); it does not apply now.
Pocket rebuild scope: U9 move; SCL via move + chord (In2) + F fanout
+ B staircase heal (69.35,1.40)<->(70.875,2.625); SDA via move +
F stub + In2 hop (69.4,2.2)->(70.2,2.5)->(71.125,1.875) + B join;
GND tree re-lay to EP (67.25,2.75); TMP_ALERT re-fan (66.275,3.4)
->(66.625,2.875); +3V3A feed to U9 pad (68.225,2.75).

## Re-lay set for the landing pass (exp241)
1. PG B braid: 23 segs margin<0 vs pair B copper (3 staircase
   strands: S (66.4-68.4,2.1-3.9), W (63.4-65.6,4.9-7.1),
   N (62.9-65.1,12.1-14.4)); detours on B vs final pair fences.
   PG chain endpoints: vias (55.125,27.125), (65.625,14.875),
   (69.625,16.375), (74.625,-15.375); branch node (60.625,9.875).
2. +3V3D F web at U5 (P3F: F segs/vias, centres x[68,77] y[19,27])
   — re-lay in leftover space after CLK/DATA arrivals.
3. XO In2 web (box x[66,76] y[16,23]) — re-lay XO's chain segment
   in leftover space.
4. Pocket rebuild (above).
5. DATA entry through the slot (fine A* in rebuilt-pocket model),
   spliced to DATA30 at (65.35,4.65).
Landing target: unconnected 5 (CDR_LOS, PHY_1V8A, STP, XI, USB_RST),
violations 4 J1. exp241esc refereed state (start point): 12
unconnected items, 10 violations (4 J1 + 4 via_dangling +
2 track_dangling — the dangling esc/SDA/SCL ends the heals consume).

## Tools
t_au1 pair ablation; t_au2 PG-combo A* (CLK B ride); t_au3/au4/au6
exact checks (decimation artefact found: emit DENSIFIED polylines,
collinear-only simplification); t_au7 arrival A*; t_au8/8c arrival
widest (+3V3D web is the arrival key: FULL -0.100, web out -0.000
with pads kept, web+XO out +0.150); t_au9 CLK settle; t_au10/10b/11
DATA widest+ablations; t_au12 entry probes; t_au13/13b fine entry A*.


---

# CLOSING UPDATE — au session end (2026-11-09). Supersedes the state claims above.

Frontier unchanged: **exp240 / pass 209** (KiCad DRC 7 unconnected, 4 violations
— all J1-intrinsic copper_edge; check_pcb 7 nets, census 109, courtyard 0,
blind SH1-only). No pass banked this session. All au evidence committed
(route mwork9, merged to origin 2868826).

## Model state (emit-ready except two joins)

Current manifest: `build_au97.json` (= au93 + detour_RBIAS_tail), full exact
gate **0 failures**. Loader/applier pattern and NET_HW table: t_au97_phase2y.py.
Emit set verified complementary by census (t_au96): clk9's missing In2 middle
IS arr_clk; data_tail's missing In2 NE run IS arr_data. No duplication.

SOLVED in the model:
- CAP pair by layer separation: CLK = pocket via (70.2,1.8), exit via
  (69.075,2.8), B ride (clk9), arr_clk In2, F arrival to U5.5; DATA =
  data_entry (pure In2), data_tail, arr_data In2, B/F arrival to U5.3.
- Pocket v6: U9 pads −1.25 x. SCL via (69.35,1.4) + bheal; SDA via
  (69.05,2.05) + hop (re-planned vs exit via, +0.121); SCL fanout v9
  (single via (69.3,1.25), flat ride y1.63, stub x66.15 into the pad rect;
  worst +0.010 vs GND chain) — SOLVED t_au92.
- Heals: +3V3A heal1 (F staircase) + heal2 (big-box A*); PG_3V3 detours ×2;
  +3V3D detours ×9 (1–5, L0–L3); ULPI_DIR dive-to-B (+0.007 vs NXT via);
  detour_XO_1/2 (notch stubs); FIXED re-lays (TMP_ALERT, SDA stub/staircase).
- RBIAS B tail (70.125,20.125)→(69.625,20.625) emitted — a REDUNDANT path:
  the In2 tail segs were NOT ripped (t_au97 matched pool tuples float-exact
  and missed; census prints rounded values). RBIAS is connected either way;
  the In2 corridor is NOT freed. Rip by rounded-coordinate match next time.

## OPEN 1 — XO bridge (arrivals + XO REF-rips are one package)

XO has 2 fragments in the model because arr_data/arr_clk were planned with
XO's staircase REF-ripped (13 rip2 items). Without a bridge the build cannot
emit the arrivals. Attempts: designed bridges v1–v10, single-via family
(exhaustive grid, 0 candidates), all-pairs A* (10/10 pairs NONE, t_au95).
Configuration is SEALED on all three layers:
- In2: RBIAS's 17-seg staircase (73.875,12.875)→…→(69.625,20.625) braids the
  knot band diagonally; its via bubble (r0.3, needs 0.6) covers frag-44's
  only join point (68.875,20.375); DM_PHY staircase parallel E.
- B: DP_PHY staircase (68.875,20.125)→(69.375,19.625), DIR diagonal
  (71.375,19.125)→(68.875,29.0), DATA via (72.6,19.3), PHY_1V8/+3V3D fat
  vias (71.375,17.625)/(70.875,15.875) r0.4.
- F: arrivals' F runs y21.7 (CLK) / y21.9 (CLK), REFCLK via (71.875,23.375),
  GND pads (70.775,19.5)/(70.825,21.0).
NEXT GEOMETRIC CHANGE (in order):
1. Wholesale RBIAS staircase re-lay In2→B: dive via near (73.7,13.1)
   (re-gate vs PHY_1V8's B journey), B ride NW roughly along the staircase
   line to the existing via (69.625,20.625) (B fences checked by hand:
   DIR diagonal stays ≥0.8 away, DP_PHY B staircase ≥0.6 E-clear, PHY B
   journey ≥2.0 E-clear), rip all 17 In2 segs (rounded match), re-lay its
   F tail as-is. Then re-gate XO dip v7/v10 geometry — the In2 band
   y19.5–20.6 x69–72 is then fenced only by arr_data and the RBIAS via
   bubble, and the dip passes S of both.
2. Fallback: re-place X1 (frees frag-96's whole web geometry).
3. Last resort: re-plan arr_clk's tail (it owns the y21.9 F run + via
   (70.1,21.8)) to open an F bridge slot.

## OPEN 2 — +3V3D stub join (decap pad (72.725,20.5))

Fragment = pad (72.725,20.5, pair GND (74.275,20.5)) + 3 F segs, term
(72.375,21.125). A* NONE: all 8 terminal pairs at hw 0.15 and 0.125
(t_au95), and direct A* to U5's +3V3D pad (76.525,24.115) at both widths
(t_au97). Fences: GND pad (70.825,21.0), CLK via (70.1,21.8) + CLK F runs,
ULPI_NXT In2 diagonal (crosses x72.375 at y21.32 — any via at the term is
inside its clearance), XO B vertical x72.625 (y20.375–24.625), DATN/DATP
U5 fanouts, SQUELCH F vertical x73.625 (y22.625–25.375).
NEXT GEOMETRIC CHANGE:
1. Re-plan arr_clk's tail dive from (70.1,21.8) E-ward (frees the
   GND-pad/CLK-via slot for an F ride term→X2.4 (70.45,22.925)).
2. Or re-place the decap pair off the (72.725,20.5) site.
Note: U5 W column resolved by census (t_au96): DATN 20.305, DATP 21.575,
CAP_DATA 22.845, +3V3D 24.115, CAP_CLK 25.385, CLKP 26.655, CLKN 27.925,
all x76.525, pitch 1.27.

## Build notes (when both joins close)

Build from exp241esc per the au build recipe: capture netcodes before
ripping; move U9 −1.25 x; rip base RIPS (t_au71 head) + rip2 (rounded
match, ALL layers, assert victim counts); emit build_au97 journeys at
manifest hw (densified polylines) + FIXED + extra; check the CAP_DATA
U6.35 pad link on the real board first (model pool shows no incident seg
but esc DRC groups them); zone refill; save as exp241; reload census diff;
BOTH referees. Landing target: unconnected 5 {CDR_LOS, PHY_1V8A, ULPI_STP,
XI, USB_RST}, violations 4 J1, silk 0, census 109, courtyard 0.
SCL endpoint-census shows 4 fragments by design (fanout stub ends inside
the pad rect — endpoint census cannot see it); KiCad DRC arbitrates.

## Traps recorded

- au94's "xo_bridge" is a frag-96 SELF-join (goal was frag-96's own
  staircase joint) — discarded; build lineage is au93 → au97, never au94.
- seg_margin deducts hw+hw+pair_clr (0.425 total vs a 0.125-hw neighbour).
- Pool items carry unrounded floats; census/fmt print %.3f — match rips
  by rounded coordinates.
- 6e46d11's commit message overclaims t_au74 results (fabricated summary;
  the process was SIGTERM-killed by a VM replacement; log is the record).
