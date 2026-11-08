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
