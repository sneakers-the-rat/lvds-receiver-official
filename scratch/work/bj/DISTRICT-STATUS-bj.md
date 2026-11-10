# USB_RST — DISTRICT STATUS (bj, 2026-11-10)
Frontier exp257 (pass 219). USB_RST NOT connected; no pass banked;
board untouched (all work was exact-geometry pricing; no exp258 was
built — every journey topology prices a same-layer crossing or a
clearance seal, and laying it would only reproduce the model's
negatives as DRC violations / save-rename shorts).
Pricers: scratch/work/bj/bj_price.py (In2-channel composite),
bj_price2.py (B-channel composite + DIR/NXT search); facts:
bj_facts.py, bj_facts2.py (+ outputs). Referee margins (0.20/0.25).

## VERDICT: the composite fails on the JOURNEY. Only U7 re-place
## remains (arithmetic below).
bh's arrival stands (re-priced here: CK via (75.44,6.04) d0.5, RST
surface via (74.80,5.82) d0.40 — all pairs >= -0.03, the two worst
being census-class vs power at DRC-legal edges). The dive opens
exactly as bi said (below). But no legal path exists between the
dive district and the arrival pocket within the authorized movable
set {DM_PHY loop, DIR, NXT, RBIAS via+column, CK escape, PHY notch
via}. The seals are made of items OUTSIDE that set.

## What works
- DM_PHY F loop re-lay west: (73.562,17.0)->(73.15,17.15)->
  (72.82,17.6)->(72.82,18.5)->via (73.625,19.125). Worst pair
  -0.030 vs GND via (73.434,17.685) — one more 0.03 west nudge of
  the bend closes it. Dive via (74.45,18.25) d0.5 then stands at
  bi's +0.425.
- DIR/NXT re-fan: NOT fully solved under the stub family searched
  (single-midpoint F stubs, single-seg B/In2 rejoins; via-only
  candidates DIR 7 / NXT 30, no pair+stub >= -0.05). Moot: with no
  journey, a dive fanout has nothing to feed (bh's position).

## The journey seals (the binding fences)
West In2 channel (bh lever 2), x-window between RBIAS and CK:
CK column x74.625 (hw0.125) caps an RST track centre at
74.625-0.125-0.20-0.10 = **74.20** for all y in [6.375,13.5].
1. **RBIAS via (73.875,11.625) d0.6** (must move for lever 2):
   its track-exclusion disc (r 0.30+0.10+0.20 = 0.60) demands
   RST centre x >= 73.875 + sqrt(0.60^2 - dy^2); at y=12.1 that is
   **74.24 > 74.20** — the disc and the column overlap by 0.04
   even before the column shift is considered. The via itself
   has NO legal destination: west/north-west is XO (via-via/track
   exclusions: XO column x73.125 spans y[11.375,15.875], XO via
   (72.125,9.875) d0.6; best western spot (73.575,10.95) is +0.019
   vs XO endpoint but -0.62 vs the +3V3A via); north is the
   +3V3A via (see 2) — via-via exclusion 0.30+0.40+0.25 = 0.95
   around (73.625,10.625) covers every northern candidate by
   >= 0.6; east is the channel itself; south is its own column.
   A south-turn tap at (72.95,16.85) prices +0.01 vs DM_PHY's
   F vertical but its F feed run west of U7 crosses the +5V F
   horizontal (72.812,13.75)->(73.562,13.75) and the DP_PHY F
   horizontal (72.312,15.25)->(73.562,15.25) on F. Dead.
2. **+3V3A via (73.625,10.625) d0.8** (not in the movable set):
   track-exclusion r = 0.40+0.10+0.25 = 0.75. At its latitude the
   channel would need x >= 74.375 (east) vs the 74.20 cap, or
   x <= 72.875 (west) — the west detour at y~10.3-10.6 runs into
   XO's In2 diagonals (72.375,10.125)->(72.875,11.125) and the
   GND via (72.9,9.45) d0.5 (west column at x72.7 prices -0.35
   vs it; at y9.875 XO's own via (72.125,9.875) d0.6 caps x <=
   71.53). At the CK jog latitude y10.35 the two exclusions are
   exactly complementary: +3V3A demands x >= 74.32 or <= 72.93,
   the CK jog seg (74.32,10.2)->(74.625,11.0) demands x <= 73.97.
   Empty.
3. The CK jog cannot be straightened to relax the cap: PHY_1V8A
   notch via (74.99,10.28) has no eastern landing (priced:
   (75.35,10.85) is -0.245 vs +3V3A F track (75.125,11.125)->
   (74.25,10.625), -0.105 stub vs +3V3A pad, -0.049 B head vs
   XI B ride; PV (75.82,10.30) d0.5 fences the rest).
B channel (priced in full, bj_price2): RST on B at x~74.5 clears
both via discs (+0.025/+0.125) but **PHY_1V8A's B journey**
(notch via (74.99,10.28))->(75.0,11.5)->(74.45,12.1)->
(73.50,12.55)-> west web to x72.35 is a continuous same-layer
barrier across the channel (-0.400 at the crossing); east of the
notch via the XI B ride diagonal (75.32,12.75)->(75.82,10.30)
and the notch B head x75.0 fence the detour, and any B<->In2
transition via inside the waist hits the same 74.20/74.475
column pair (a d0.5 via needs 1.15, the waist offers 0.925).
North end of the B channel also crosses +3V3A's B diagonal
(-0.167) and SCL's B staircase (-0.425 at x75.95).
Far-west B (bi: columns 67.15/67.9/70.15/70.7 all dead) and the
east In2 corridor dead-end (bh) stand as priced before.

## Conclusion
Within the movable set, the U7-west district is a four-layer
seal for U7.9 -> U6.40: F by the pad rows + EP grid, In2 by the
RBIAS-via/CK-column and +3V3A-via/CK-jog disc pairs, B by
PHY_1V8A's B journey + the +3V3A B web + SCL staircase, In1 is
the GND plane. The remaining geometry change is bh's lever 3:
**re-place U7** so its reset pad faces a different district
(~40 nets re-fan; everything else about the design is done and
bh's arrival geometry moves with the chip). Until that is
authorized, USB_RST stays the last net: exp257, DRC 4 J1,
check_pcb nets 1 {USB_RST}, census 120, courtyard 0.
