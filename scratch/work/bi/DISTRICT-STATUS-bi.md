# USB_RST — DISTRICT STATUS (bi, 2026-11-10)
Frontier exp257 (pass 219). USB_RST NOT connected; no pass banked.
Board unchanged. All numbers exact-geometry (hw/gridroute.py item
model) under referee rules (0.20 / 0.25 power). Pricers:
scratch/work/bi/bi_price.py (V1–V4 composites), bi_grid.py,
bi_divegrid2.py, bi_opt.py, bi_opt2.py (+ facts in bi_facts_out.txt).

## VERDICT: lever 1 (DIR+NXT re-fan) does NOT open a dive.
bh's arrival stands (not re-derived, not built — pointless without a
dive). The dive is a closed 3-via packing problem, proven four ways:

1. Lever-1 MAX grid (DIR+NXT south escapes DELETED entirely, dive via
   gridded x[73.6,75.3] y[16.95,19.3]): exactly ONE legal slot —
   (74.85,17.45) d0.5 at +0.116 (fence: XI B seg), d0.40 at +0.166.
   Everywhere else fails; the west jaw is closed by arithmetic:
   GND pad corner (74.625,16.875) to DM_PHY diagonal endpoint
   (74.125,17.375) is 0.707 apart < 0.40+0.50 of the two exclusion
   radii for even a d0.40 via.
2. Re-placing the neighbours around that slot kills it:
   - DIR via IS placeable: (74.85,18.40) at +0.024 (tail
     (75.42,17.95)->via, B via->(73.30,18.42)).
   - NXT via is placeable NOWHERE once the RST dive exists: its
     d0.5 annulus (≥0.70 from (74.85,17.45)) excludes the whole north
     pocket (75.2–75.4, 17.1–17.4 all ≤0.55 away); the south pocket
     (74.85,19.15) is F-stub-unreachable — the DIR-via→XI-via stub
     slot is 0.925 wide (DIR via x≥74.70 forced by DM_PHY's F
     vertical) vs 1.10 needed; east approach dies on XI via
     (75.625,18.625) d0.6 track-disc; NXT's In2 leg from any north
     via runs SW through the dive disc (0.55 track exclusion).
   - Independent grids (bi_opt): NXT set best −0.175 (both boxes).
     Joint random search, 1500 triples with bent stubs (bi_opt2):
     best −0.242.
3. The fence bh's lever-1 analysis did not name: **DM_PHY's F loop**
   — vertical x74.125 (y17.375–18.625) w0.25 + diagonal
   (74.125,17.375)->(73.5625,17.0). It walls the west side of every
   dive candidate (dive via (74.30,17.50) prices −0.400 against it)
   and forces DIR's via east, closing the DIR–XI stub slot.
4. Journey (moot, but priced): west B is a woven web — columns at
   x70.7 / x70.15 / x67.15 all die (−0.37..−0.65) on +3V3A B
   diagonals/horizontals, PHY_1V8A B, DAC_SYNC via (70.7,7.8) +
   DAC_SYNC F pad rect (69.975,7.1,71.425,7.4), +3V3D/GND via rows
   at y15.125–16.9, SPI_SCK via (67.8,8.1). East legs at y3.9–4.5
   cross I2C_SCL/SDA B staircases (−0.40..−0.425). No west B column
   was found; the x≈69.65 residue from bh is inside the same web
   (its column crosses +3V3A B (70.5,11.125)->(68.875,12.375) and
   the DAC_SYNC picket pair (69.51,7.85)/(70.7,7.8), whose 1.19
   spacing admits a track (0.55+0.55) but no via pair (1.40)).

## NEXT GEOMETRY CHANGE (needs parent/user authorization)
A. **DM_PHY F loop re-lay** (was in bd's original scan set, not in
   bi's brief): with DM_PHY's loop deleted as well, the dive grid
   best is (74.45,18.25) at **+0.425** d0.5 — a real slot with room
   for the DIR/NXT cascade to re-form west of it. This is the
   binding fence; opening it re-opens the whole fanout question.
B. bh's lever 2 (RBIAS via (73.875,11.625) west + column shift) —
   untested here; it addresses the In2 waist, not the dive, so it
   only matters after A.
Until one is authorized: USB_RST stays the last net. Board state
unchanged (exp257, DRC 4 J1, check_pcb nets 1 {USB_RST}).
