# SWCLK survey (aj session, 2026-11-07) — queue item 2, not landed

SWCLK: U6.109 (90.750,−16.663) ↔ J4.4 (92.520,−23.520), bare pad,
zero copper. Target is the debug header ~7 mm SSE.

Dive window south of U6.109 is triple-sealed (exact-model
arithmetic, this session):
- DAC_SYNC via (90.125,−17.875) d0.6 — track shadow 0.60, via
  shadow 0.75 (pair 0.2).
- +3V3D In2 vertical x91.375, w0.6, y[−21.875,−15.125] — via
  shadow: centres x ≤ 90.575 (dist_to_item ≥ 0.25+0.25).
- R16.2 GND pad (90.575,−19.000) 0.80×0.95, rect
  x[90.175,90.975] y[−19.475,−18.525] — via shadow: 0.45 from rect.
DAC via + R16.2 + +3V3D vertical pairwise overlap the whole
window: best candidate (90.5,−18.6) is inside R16.2's rect;
(90.55,−18.05) fails R16.2 by −0.125; the In2 TRACK thread at
x≈90.7 exists (+0.005..+0.02) but there is no via to reach it.
(SWDIO's F vertical is at x91.375 w0.25, y[−19.625,−14.125] —
the brief's x91.075 was wrong; +3V3D's In2 vertical shares the
x91.375 line.)

Vehicle: neighbour relay = relocate DAC_SYNC's via west/south
and place SWCLK's via jointly (2-via optimization against
R16.1 BOOT0 pad (88.925,−19.000) rect x[88.525,89.325]
y[−19.475,−18.525], R16.2, +3V3D vertical, SWDIO F vertical).
Hand-derived feasible pair: DAC via (89.8,−18.35) d0.6
(R16.1 margin +0.006) + SWCLK via (90.5,−18.0) d0.5 (DAC +0.03,
+3V3D +0.075, R16.2 +0.075) — knife-edge, needs the optimizer
treatment (t_ai11 pattern) plus DAC_SYNC's F stub re-lay
(90.250,−17.163)→new via and B seg new via→(90.125,−16.125),
then SWCLK's onward journey SSE on In2/B to J4.4 (not surveyed
past the window; SWDIO's F chain runs (91.375,−19.625)→
(90.375,−22.375) across the natural F path, so the journey is
In2/B with a late dive near J4).
Alternative: jog +3V3D's In2 vertical east at y[−17,−19.6]
(rejected on survey: jog vias land on SWDIO's F vertical line
x91.375 = short; offsetting them re-opens the whole puzzle).
