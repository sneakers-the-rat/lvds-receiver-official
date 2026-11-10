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
fix1's 5 new items = gate hole: new-track vs new-via cross terms unchecked. fix2 fixes gate + geometry:
- STP via (76.065,17.96)->(76.6,17.8): DIR lane cannot pass between NXT bend pt (75.45,17.32) and STP via (needs 0.95, gap 0.888) nor south of it (X1 pad). DIR F re-lane north of new via.
- CK via ->(77.5,17.95); GND stitch via ->(78.15,18.35).
- +3V3A via (77.862,10.975) DELETED (redundant feed; In2 web fed from north via (76.625,10.5)->(78.0,16.375)).
- C22 moves (77.17,9.95)->(77.45,9.6): un-braids XO (C22.1 NW corner sat on XO's only lane). PHY via ->(78.25,9.95), GND tie via ->(76.7,9.25).
- South lanes (parallel, no crossings): A west, XI mid, XO east-then-west, +3V3A SW west.
