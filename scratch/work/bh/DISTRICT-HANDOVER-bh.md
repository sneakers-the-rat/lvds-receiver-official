# USB_RST — priced fence map (parent, 2026-11-10 ~02:20, from exp257)
Pricer: scratch/work/parent-shots/price_rst.py + price_arrival.py
(exact geometry via hw/gridroute.py load_items + pair/via rules).
All margins below are exact-geometry, referee-class rules.

## Confirmed dead (do not re-derive)
- F arrival into U6.40 (74.75,4.662; pad rect x[74.60,74.90] y[3.922,5.402]):
  south-end entry window is x in [74.750,74.756] at the end edge only —
  a 6-micron lens between U6.39's pad (rect x<=74.4, +3V3D, power class)
  and ULPI_CK via (75.125,5.875) d0.6 (0.60 exclusion). No legal F
  traverse to the pad exists. West face fenced by U6.39's F escape
  (x74.25, y3.16-4.66); east face by U6.41 (ULPI_CK) pad rect
  x[75.1,75.4] y[3.925,5.4]. Via-on-pad impossible (d0.5 via breaches
  pin-39 clearance at every pad position, best -0.05).
- Surfacing-via grid x[73.85,75.65] y[5.5,7.3] (0.15 step): BEST score
  -0.15. Every candidate fenced by CK via, I2C_SCL B diagonal
  (74.375,6.125)->(74.625,6.375), or BIST_DRV In2 staircase.
- In2 vertical in the waist: RBIAS In2 column x73.875-74.0 (y11.6-16.5)
  vs ULPI_CK In2 column x74.625 (y6.375-13.5, jog west to 74.32 at
  y9.4-11.0). Waist 0.625 wide, In2-In2 pass needs 1.05. IMPOSSIBLE.
- In2 west column x72.3: fenced by XO In2 x73.125 (y11.4-15.9),
  +5V via (72.2,13.1), RBIAS westward top tail y~17.1 x73.1.
- B layer: +3V3A B horizontal y8.625 spans x68.6-75.6 + diagonal
  (73.625,10.625)->(75.625,8.625) fences every B crossing; east B
  fenced by ULPI_STP B chain x76.05-76.35 + XI pocket via (75.82,10.30).
- In2 south band fences: BIST_DRV staircase (73.125,6.875)->(75.875,4.625)
  45deg; SPI_MOSI In2 (73.4,5.2)->(75.1,4.55); DAC_SYNC In2 diagonal
  (71.375,5.875)->(75.5,3.5); +3V3D In2 (74.25,3.5)->(72.875,3.375).
- Dive via at U7.9 pad (74.25,16.438) d0.5: GATES (not in any negative
  list). In2 exit NE to (74.55,15.7) also gates.

## The build that exists (composite, all moves authorized)
Posture law + user 2026-11-10: purple/In2 traces movable; parent
authorized ULPI_CK U6-side escape move (via + first In2 leg).
1. ULPI_CK via (75.125,5.875) -> approx (75.45,5.9) (exact-gate it).
   F escape from U6.41 pad extends east/south to the new via.
   This opens the U6.40 south-end entry: at y5.6 the legal centreline
   lane becomes x in [74.75, 74.93]; surface via approx (74.72,6.2),
   F hop (74.72,6.2)->(74.78,5.45)->pad end. Price all of it exactly.
2. ULPI_CK In2 escape re-lay from the new via west to its column
   x74.625 — must thread between +3V3A staircase (x75.55, y6.75-9.0)
   and BIST/SCL corner cluster (74.625,6.375); a south bow is likely.
3. USB_RST journey = USER'S design: dive at U7.9, In2 near-vertical
   south... north to the arrival. The waist forces ONE deviation:
   cross CK's column band on In2 only where CK's re-laid escape/jog
   leaves a slot, or cross under the column's south end (y<6.375)
   through the space the CK escape vacates. Design it in exact
   geometry against the CURRENT board + your own CK re-lay, build,
   referee. BIST staircase pieces and SPI_MOSI In2 segment are
   approved nudges if the exact gate asks for <=0.6mm shifts.
4. Referee: KiCad DRC + check_pcb. Bank pass 220 at nets 0,
   DRC 4 J1 only. Then STOP and report.
