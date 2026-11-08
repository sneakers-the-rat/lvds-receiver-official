# DISTRICT-STATUS-4 — ak session handovers (exp221 stands)

Two queue items proven blocked this session with exact-item-model
evidence. Neither was banked; no copper moved. Scripts:
scratch/work/ak/t_ak1..t_ak7.

## 1. GND U6.38 / zone<->zone item — NOT the cheap stitch it looked like

Island census (t_ak2_islands.py, F layer): the GND F zone has 24
fill outlines; every outline but one contains a GND via (its stitch
to the In1 plane). outline20 (bbox x[73.65,73.85] y[3.83,5.45],
U6.38 only, NO via) is KiCad's zone<->zone item. (outline23/U6.31
also lacks a via but is healed by pass 185's GND track tie.)

Every local heal is fenced (t_ak1 dump, arithmetic by hand):
- Stitch via: the channel between U6.37's pad east edge (73.40) and
  U6.39's pad west edge (74.10) is 0.70 mm; a d0.5 via needs 0.90
  (0.25 r + 0.20 clr each side; worse vs +3V3D at the 0.25 power
  class: centre >=73.85 from the west fence, <=73.60 from the east —
  contradiction). d0.4 fails (0.15 gap); d0.3 fails the 0.3 min
  hole. Via-in-pad and N/S pad-end positions all fail named fences
  (ULPI_D0's diagonal, +3V3D's w0.6 staircase). No GND fill exists
  within reach N or S of the row to tie to (probed 6 points).
- Track tie on F: west = ULPI_D0's pad; SW/S = +3V3D's staircase
  band (channels 0.245-0.25 vs 0.60 needed); NW channel between
  D0's pad top (y5.40) and its diagonal = 0.25 vs 0.60. A shared
  y~5.9 channel (GND w0.2 + D0 w0.2) fails by 0.075: centrelines
  confined to [5.70,6.025], need 0.40 apart, have 0.325.
- ULPI_D0 dive (to free the F channel): joint search t_ak4 over 9
  DAC_SYNC In2 staircase shifts x D0 dive grid = ZERO feasible
  dives. Margin map t_ak5: best dive points in x[72.4,74.6]
  y[5.2,6.6] are -0.142, blocked on B by I2C_SCL's B staircase,
  -0.16..-0.20 on In2 by DAC_SYNC's staircase. CK cannot dive
  earlier (its via (75.125,5.875) is wedged by the same 0.5-pitch
  arithmetic; trial points fail HV_SHDN's pad by -0.073/-0.086).
  D0 cannot dive at its corner (73.25,5.662) (-0.013 vs U6.38's
  pad), west-shifted (fails In2 vs DAC_SYNC), or at (74.125,5.875)
  (BIST_DRV's In2 seg starts exactly there — a via shorts D0 to
  BIST_DRV on In2). NE rejoin points fail B vs I2C_SCL by -0.021.
- GND F flood from the island pad (t_ai13 pattern): 1 cell.

Verdict: item 1 is a FOUR-net braid (ULPI_D0 x DAC_SYNC-In2 x
I2C_SCL-B x I2C_SDA-B) plus the +3V3D F web — it needs the full
connection-order re-derivation of the U6 north-mouth district
(the "two-net relay" of the standing note is this job, at full
district scale), or a placement-level answer. Do NOT attempt
another local stitch; the arithmetic above is exhaustive for
single-net moves.

## 2. PHY_1V8A option (d) — SE-lobe re-solve FAILED with proof

Model (t_ak6_solve.py): exp221 + t_aj7's proven PHY_1V8A design
emitted in-model (notch via (75.7375,10.75), B journey, SCL via
-> (69.5,12.75), +3V3D via shrunk d0.5) + XO tail ripped.
Variables searched: +3V3A S1 In2 cluster west shift s in
{0,.125,.25,.375,.5}; PHY_1V8 B-return corner (76.8,10.988) shift
(de,dn) in {0,.125,.25}x{0,-.125}; PHY via P micro-shift in
{(0,0),(-.0625,0),(0,-.0625)} — 90 combos; XO dive X scanned on a
0.0625 grid over x[76.15,77.05] y[10.30,11.05], gated on all 3
layers + XO's F stub. Survivors: ZERO.

Margin landscape (t_ak7_lobescan.py, wider box): best achievable
min-margin over all combos ~= -0.20. The lobe is fenced on every
layer at once by independent items:
- F: C16.2's GND pad (76.775,9.75), rect y<=10.225 — a d0.5 via
  needs centre y>=10.675 inside its x-range; PHY_1V8A's notch via
  (75.7375,10.75) needs >=0.70 centre distance; U7.28/U7.26 pad
  rects shadow the whole y>=10.82 band outside U7.27's own pad
  x-range, and inside it both neighbours fail by -0.10.
- In2: +3V3A's S1 seg (77.125,13.125)->(76.625,10.25). Shifting it
  west helps X's gate (-0.60 at s=0 -> -0.237 at s=0.5, point
  (76.588,10.475)) but eats PHY_1V8A's notch via on the same
  layer: VP2's In2 margin vs S1 is +0.189 at s=0, -0.398 at s=0.5,
  zero at s~=0.16 — where X's In2 margin is still ~-0.51. The two
  constraints are opposed along one seg and their sum is negative
  for every s: no (s, X) pair satisfies both. PROVEN, not sampled.
- B: PHY_1V8's w0.6 return seg (77.35,10.0)->(76.8,10.988);
  shifting its corner east/north gains ~0.03 only (B margin
  -0.236 at the best point).
- A west dive (x<75.7) also dies: B vs PHY_1V8A's own B journey
  first seg (-0.124 at (75.1,10.9)), and XO's B flood from there
  cannot cross PHY_1V8A's journey to reach (74.125,12.25).
- d0.4 vias are not a way out: drill 0.3 (board min hole) gives
  0.05 annulus < the 0.1 the d0.5/drill0.3 standard implies.

Verdict: option (d) cannot free the notch. PHY_1V8A remains
blocked on the USER decisions already on the table: (e) relocate
C16, or (f) leave one of XO/PHY_1V8A unconnected. The proven
t_aj7 design still emits verbatim the moment the notch frees by
either route. Q micro-adjust was not searched: Q's fences are
>=1.0 mm from every lobe point and cannot bind.

## 3. SWCLK — DAC-move + dive pair PROVEN empty (t_ak8_swclk.py)

Optimizer scan on exp221 (DAC via ripped in-model, d0.6; SWCLK
dive d0.5; both gated on 3 layers + stubs; journey floods on B
and In2 to J4.4): DAC_SYNC's via has only 12 feasible positions,
ALL within 0.13 of its current (90.125,-17.875), best margin
+0.017 — it is pinned by R16.1/R16.2/U6.110's pad. (D,S) pairs
passing via+stub gates: ZERO. With D pinned at the window's west
edge, its 0.75 via-via exclusion covers the whole SWCLK window
(+3V3D In2 vertical caps S at x<=90.575; R16.2's rect caps S at
y>=-18.075 in range; the two caps leave only points <0.75 from D).

The aj survey's hand pair is REFUTED: DAC at (89.8,-18.35) gates
+0.006 vs R16.1's CORNER but -0.086 vs R16.2's pad (corner dist
0.414 - 0.30 - 0.20) — the survey gated DAC vs R16.1 only.

F-jog escapes were hand-checked and each dies on a named fence
within two moves: the strip south of U6's row is sealed
x[89.5,90.7] for all y in [-17.7,-18.475] by DAC's via disc
(r0.60 for tracks) union R16.2's shadow (from y-18.225); the
x[89.625,89.875] slot between R16.1's and R16.2's shadows is
reachable only through that disc. Between-pad channels in the
0.5-pitch row are impossible (0.2 gap vs 0.6 needed).

Remaining vehicles (not attempted): (i) DAC_SYNC west-dive
re-lay — F strip run west at y~-17.75 (gates +0.047 vs the row
pads) to a dive ~x87.5, B seg rejoining its chain at
(89.625,-15.625), old B chain ripped back from (90.125,-16.125);
then SWCLK's window has no DAC via in it. (ii) SWDIO staircase
re-lay as a third net. Either is a full district job.
