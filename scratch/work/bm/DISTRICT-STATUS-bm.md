# DISTRICT STATUS — bm (USB_RST endgame, inherited from bl)
Updated: 2026-11-10 ~06:00 PST. WORKING STATE — updated as I go.

## Inherited state (verified from disk)
- bl re-placed U7 +0.75 EAST (76.00,14.00) -> (76.75,14.00); C19 also moved
  (+0.35 per build v3 title; verify from board). Price: +0.75 = 0 pad-rect
  collisions; +1.0 collides U7.24/ULPI_D0 vs C19/NRST.
- exp259 = the move (check_pcb: nets 1 {USB_RST}, census-class clearance
  lines 319 incl. standing HV/GND census bands — NOT comparable to DRC).
- exp260 = fix1 repairs (check census 247). exp261 = fix2 (south fanout,
  east vias, NE braid): KiCad DRC 109 = 71 clearance + 18 shorting +
  8 solder_mask_bridge + 5 hole_clearance + 4 copper_edge (J1) +
  2 track_dangling + 1 tracks_crossing; DRC unconnected 1.
- bl local commits through 7cdd9701 were NOT on origin (diverged by bk's
  merge commit f6ab8411). bm MERGED f6ab8411 into bl's HEAD -> 912d900f,
  PUSHED; origin/main = 912d900f verified. Boards byte-identical across
  the merge (only schematic-side files came in).

## Plan
1. Verify exp261 first-hand (reload census + DRC re-run). [DOING]
2. Repair re-fan damage -> nets 1 {USB_RST}, DRC 4 J1 only, courtyard 0.
   Bank pass 220 via scripts/commit_pass.py.
3. Build USB_RST through the opened district: dive per bi (DM loop
   re-laid opens dive at (74.45,18.25) +0.425 — RE-GATE on exp261's new
   geometry, U7 moved +0.75E so all U7-side coords shifted); arrival
   re-solved at LEGAL d0.50/drill 0.30 vias (bh's d0.40 via is illegal;
   bk: at d0.50 the CK/RST pair was 0.677 vs 0.70 needed on exp257 —
   re-gate on the moved board). Bank pass 221 at nets 0. STOP.

## Hard facts carried in
- Board min via d0.50 / drill 0.30. No d0.40 vias anywhere.
- gridroute 0.30 In2-In2 spacing is a check_pcb census band, NOT a DRC
  gate (exp257 violates it DRC-clean) — judge by KiCad DRC + check_pcb
  nets/courtyard, not the census count.
- Save-rename is CONTACT: reload + netname-verify after every save.
- Zone refill before DRC.

## exp262 refereed: DRC 85 (55 clr, 12 short, 6 mask, 5 hole, 4 J1, 2 dangl, 1 cross), nets 1 {USB_RST}, courtyard 0
fix1's 5 new items = gate hole: new-track vs new-via cross terms unchecked. fix2 gate includes them.

## fix2 -> exp263 BUILT (gate 0 negatives; referee running)
Final design as built (all re-gated on exp262):
- North fan: NXT/DIR F re-laned; STP via ->(76.74,17.88) with F drop + B
  column rejoining at (76.425,12.9); CK via ->(77.48,17.98); CK In2 column
  re-laid west at x75.9, T-joining kept column at (76.62,16.9) (only the
  (76.62,18.3)->(76.62,17.3) seg ripped); CK In2 loop passes NORTH of the
  GND stitch via (77.25,18.38) — stitch via KEPT in place.
- +3V3A via (77.862,10.975) DELETED (redundant: In2 web fed from north).
- SW quadrant: C22 does NOT move (every move broke its GND tie or PHY via).
  XI keeps its F lane from PV; XO threads SE of XI's final seg and NW of
  C22.1's pad (PHY hop re-laid SE to widen the slot); A lane west.
- NOTE: exp263 has NO GND stitch via at (78.0,18.3) (it was fix1's
  placement; ripped in fix2 as CK's loop fences it). If check_pcb shows a
  GND split, re-stitch at a gated site.
- Gate lessons: pads must enter pools as F-only rects (EP/thermal pads are
  NOT on In2/B); gridroute track layer names ('F') vs pad layer names
  ('F.Cu') silently broke victim matching — normalized in bm_gate pool;
  +3V3D B staircase is 0.6 wide (not 0.2) — read widths from the board.
- VM replaced once mid-fix2; toolchain restored offline via restore.sh.

## Remaining for pass 220 (fix3, from drc262 items — recheck on exp263)
- NE braid: +3V3A via (78.8,11.62) shorts I2C_SCL In2 x79.125 + ULPI_D7 B;
  solve with SCL + D7 together.
- East escapes D0-D7 shear-compressed vs dive vias; re-fan at pitch.
  D3 via (80.15,13.7) shorts C48.1; D6 via (81.0,14.4) vs C48.1/+3V3D B;
  D2 via (80.3,12.8) vs C19.1 NRST; D7 via (79.1,15.88) vs SCL staircase.
- C48/C19 local: +3V3D F track vs C19.1 NRST pad.
- +3V3A dangling In2 stubs at (77.625,15.875), (78.125,16.375).
