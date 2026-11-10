# USB_RST — DISTRICT STATUS (bh, 2026-11-10)
Frontier exp257 (pass 219). USB_RST NOT connected; no pass banked.
All numbers exact-geometry (hw/gridroute.py item model) under referee
rules (KiCad edge classes 0.20 / 0.25 power) unless marked "router"
(gridroute In2-In2 0.30 census band — NOT a violation gate: banked
exp257 itself carries BIST-MOSI at router-margin -0.065).
Pricers: scratch/work/bh/design_bh.py, design_bh2.py, design_bh3.py
(+ _out.txt each). Facts: facts_bh.py, facts_east.py, facts_q.py,
facts_south.py, facts_west_b.py (+ outputs).

## CORRECTION to the parent handover
"Dive via at U7.9 pad (74.25,16.438) d0.5 GATES" is WRONG. It prices
-0.211 vs RBIAS In2 (73.925,16.275)->(73.9,16.3) and -0.075 vs U7's
GND pad rect (74.625,16.0)-(74.875,16.875). The parent's pricer
sliced it out of the displayed worst list. See DIVE below.

## ARRIVAL at U6.40 — SOLVED (design exists, not built)
- ULPI_CK via (75.125,5.875) d0.6 -> (75.44,6.04) **d0.5** (d0.6 does
  not fit: RST-via/CK-via pair needs 0.70 at d0.5/d0.4, 0.75 at
  d0.6/d0.4; best d0.6 pair distance found 0.677).
  F escape (75.25,5.162)->(75.33,5.62)->(75.44,6.04) (one census-class
  pair vs U6.42 HV_SHDN pad corner, DRC edge 0.216 — legal).
  In2 bow (75.44,6.04)->(75.05,6.6)->(74.7,7.0)->(74.625,7.35);
  CK column seg (74.625,6.375)->(74.625,9.4) ripped, re-added
  (74.625,7.35)->(74.625,9.4). All CK pairs >= +0.005 referee.
- USB_RST surface via **(74.80,5.82) d0.40/drill 0.20** (d0.5 does not
  fit the pocket: fences CK via NE, I2C_SCL B band SE, BIST_DRV W,
  U6.39 pad W). F hop (74.80,5.82)->(74.78,5.50)->(74.78,5.30) into
  U6.40's south end. All pairs >= -0.034 (census-class only).
- Required nudges (priced): BIST_DRV window pieces dy=-0.049;
  SPI_MOSI seg (73.4,5.2)->(75.1,4.55) dy=-0.014; I2C_SCL B corner
  pieces (74.375,6.125)->(74.875,6.625) shift (-0.035,+0.035).
- The surface via's In2/B approach side: from the SOUTH-WEST on B is
  the only priced-open stub direction (SCL band fences S/SE on both
  inner layers; CK column foot fences W on In2).

## DIVE at U7.9 — IMPOSSIBLE within the move set (the binding problem)
U7.9 pad rect x[74.125,74.375] y[15.998,16.878] (south row, 0.5 pitch).
- On-pad via: neighbour pads are 0.375 from pad centre E (GND pad)
  and W (pin 8). d0.5 via margin -0.075 both sides; d0.4 -0.025;
  d0.3 = 0.000. No fab-sane via fits on the pad.
- South stub + via: fenced by ULPI_NXT via (74.94,17.36) d0.5,
  NXT In2 diagonal (74.94,17.36)->(74.10,17.70)->(74.50,19.25),
  ULPI_DIR via (74.82,18.10) d0.5 + DIR F fanout
  (75.75,16.875)->(75.60,17.30)->(75.42,17.95). Every candidate via
  in x[73.4,75.1] y[17.3,19.0] fails >= one fence by 0.06-0.39.
- W = pin 8's pad; E = GND pad; N = chip body.
- RBIAS In2 top shift dx=-0.40 (window y[15.82,16.80], 39 segs,
  2 boundary connectors — machinery verified in design_bh3) clears
  RBIAS vs a dive via (+0.045) but cannot fix the pad-pitch fences.

## JOURNEY — every topology priced dead
- In2 waist: RBIAS column x73.875-74.0 (y11.6-16.5) vs CK column
  x74.625: 0.625 wide, needs 1.05 (router) / 0.85 (referee, still
  impossible). RBIAS dx=-0.30 shift leaves CK side at -0.08.
- In2 west channel south end: RBIAS via (73.875,11.625) **d0.60**
  keep-out disc reaches x74.475 at its latitude; CK column clearance
  reaches x74.20 — seals overlap. XO column x73.125 seals the west.
- CK L-barrier (column y6.375-13.5 + horizontal y13.5 x74.625-76.62):
  B-crossing via pairs sealed at every x by U7 EP rect
  (74.45,12.45)-(77.55,15.55) + no-net EP grid pads (F obstacles,
  x74.555-76.415 y12.555-15.445), XI B ride vertical x74.98
  (y13.4-15.95), ULPI_STP B jog (76.425,12.9), CK vertical x76.62,
  +3V3A In2 trunk x77.375 w0.60. F-crossing likewise (grid pads).
- East In2 corridor x75.07 (between CK column and +3V3A staircase
  x75.55, referee-legal +0.02/+0.03) is unreachable: its south end is
  blocked by PHY_1V8A notch via (74.99,10.28) and CK horizontal.
- West B: +3V3A B web spans the west (151 segs in x[66.5,74.6]):
  horizontal y8.625 (x68.6-75.6), staircase (68.625,4.875)-
  (69.125,4.375), vertical x68.625 (y16.6-19.1); PHY_1V8A B web
  (145 segs) behind it. Three priced B journeys (columns 67.9/68.3/
  68.7, legs y4.5-4.75) all fail at -0.325..-0.65 on +3V3A/DP_PHY/
  SPI_SCK-via fences. Unpriced residue: column x~69.65 + leg y~3.9
  (hand margins +0.075/+0.025 vs the staircase) — but moot: no dive.
- Far east In2: sealed by +3V3A trunk/via (77.862,10.975),
  I2C_SCL In2 horizontal y8.375 + via (78.125,8.375) d0.6,
  ULPI_STP In2 diagonal (76.445,9.03)->(77.2,5.9).

## NEXT GEOMETRY CHANGE (needs parent/user authorization)
The dive is the blocker; the journey is moot until a dive exists.
Levers, in order of proportionality:
1. Joint re-fan of ULPI_DIR + ULPI_NXT U7-side escapes (both in the
   ORIGINAL bd-scan movable set): move DIR dive via (74.82,18.10)
   and NXT dive via (74.94,17.36) east/south-east together to open
   a dive slot at ~(74.3,17.5) south of U7.9; then the journey
   question re-opens (DIR's own B corridor proves B reaches
   (68.875,29.0); a northward B crossing at x~69.65/y~3.9 is the
   unpriced candidate).
2. Move RBIAS's via (73.875,11.625) west with its F stubs + shift
   its In2 column west 0.30: re-opens the In2 west channel
   (waist becomes referee-passable at x~74.16-74.31 except CK jog
   latitude y9.4-11.0, which then binds vs notch via (74.99,10.28)).
3. Re-place U7 (disproportionate; ~40 nets).
Until one is authorized: USB_RST stays the last net. Board state
unchanged (exp257, DRC 4 J1, check_pcb nets 1 {USB_RST}).
