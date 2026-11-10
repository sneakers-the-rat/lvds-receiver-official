# DISTRICT STATUS — bm (USB_RST endgame, inherited from bl)
Updated: 2026-11-10 ~15:50 PST. WORKING STATE — updated as I go.

## CURRENT: exp264 BUILT + REFEREED (commit 21db5163, local — push pending)
- exp264 = bm_fix2b from exp262: north fan re-lane (NXT/DIR/STP/CK),
  C22 MOVED SOUTH (77.17,9.95)->(77.05,8.9), XI/XO braid re-laid,
  PHY hop + pad26 chain re-laid, +3V3A via (77.862,10.975) + its In2
  seg DELETED (it SHORTED U7.26 PHY_1V8 — drc262 shorting_items),
  GND stitch via (78.0,18.3) and C22.2's old stub/via ripped.
- Referee: KiCad DRC 65 (35 clearance, 12 shorting, 5 mask bridge,
  4 hole, 4 dangling, 4 copper_edge J1, 1 crossing); check_pcb nets 2
  {GND, USB_RST}, courtyard 0. (exp262 was DRC 85/nets 1; exp263 70/2.)
- GND nets-2 = C22.2 islanded at its new site + zone<->zone pair —
  both named fix3 items. +3V3A is WHOLE (the deleted via was NOT
  pad30's feed; pad30/pad31 feed = row track + diagonal + west lane).
- Gate: bm_fix2b gate-clean except ONE declared exception, coded in
  the script: XI seg PV(75.82,10.3)->(76.2,10.42) vs PHY_1V8A seg
  (75.95,10.82)->(75.35,10.42) at -0.039. PV itself is 0.361 from
  that seg (< 0.4), so no track out of PV clears it; the identical
  pair is a KiCad clearance item on exp262 AND exp264 (count 1,
  unchanged). Fixing it = moving A's lane = fix3b's knot.
- Gate lessons banked this session: (1) gridroute pad items carry
  short layer names — normalize ALL item layers or pad checks never
  run (voided fix1/fix2 gates); (2) TWO silent string-replace patch
  failures (C22 pool shift; a POWER=set patch) — grep-verify every
  patch; (3) a gate is only as good as its pool.

## fix3 plan (bank pass 220 only at nets 1 / DRC 4 J1 / courtyard 0)
- fix3a: C22 fallout — D0 F staircase step (77.125,8.375)->(77.375,
  8.625) shorts C22.2's new rect: jog D0 around the rect's NE corner.
  STP via (76.44,9.03) vs C22.1 rect (clearance+hole): shift via W.
  CK In2 dangling: kept column seg (76.62,17.3)->(76.62,13.5) has a
  free end at 17.3 (my loop T-joins at 16.9) — trim to (76.62,16.9).
  C22.2 GND tie at new site + GND zone<->zone stitch via.
- fix3b: SW knot — +3V3A west lane vs PHY_1V8A lane SHORT on F
  (interleaved chords: A NE->SW via (74.99,10.28), +3V3A E->W).
  Coordinated re-lay of BOTH; ~7 items incl. the XI/PV exception.
- fix3c: NE braid — +3V3A via (78.8,11.62) shorts I2C_SCL In2 11.5mm
  seg + ULPI_D7 B trk; D7 via (79.1,15.88) shorts SCL stub + +3V3A B;
  +3V3A B crossing D7 B; ~11 items, solve +3V3A/SCL/D7 together.
- fix3d: east D-fan — D0..D7 escapes shear-compressed by the U7 move;
  sequential rip + re-fan at pitch; D3 via shorts C48.1 rect; D2 via
  vs C19.1; +3V3D F vs C19.1; +3V3A In2 dangling stubs x3. ~24 items.
- LOCAL COMMITS NOT PUSHED: cf92a91e..21db5163 (route clone). Push via
  fresh GitHub-URL clone + ls-verify refs/heads/main.

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

## 2026-11-10 ~16:55 — fix3b + fix3b2 BANKED-IN-PROGRESS (commit d9abf96b, pushed+verified)
- exp268 (fix3b): SW knot decomposition: +3V3A F web/row ripped, via31 in pad31 rect + via30, XI F rise + B ride re-laid, A F/B re-laid. DRC 54->51. New defects: via31-via30 hole_near_hole (drills 0.275 apart — gate had no via-via hole check), west +3V3A via (73.625,10.625) dangling, 4x A-seg vs XI PV clearance (A lane passes PV at 0.39-0.49 centre; F-north passage proven closed: needs y>=10.85 at x75.82 vs pad bound 10.825).
- exp269 (fix3b2): A w0.15 neck at y~10.82-10.84 over PV (KiCad edge 0.203-0.22 both sides — DOCUMENTED compromise, 0.15mm neck ~0.8mm long on PHY_1V8A), via30 deleted -> pad30 fed by F row track (75.5,11.562)->(76.0,11.562) w0.25 through pad31, west via deleted. DRC 46: clearance 29, shorting 6, hole_clearance 3, tracks_crossing 1, mask_bridge 1, copper_edge 4 (J1), track_dangling 2 (+3V3A In2 stubs). UNCONN = USB_RST only. SW KNOT CLEAN.
- Declared gate exceptions (bm_fix3b2 allowed()): A vs +3V3A pad30/pad31 rects floor -0.05 = exactly KiCad's zero (gate uses check_pcb 0.25 power rule, KiCad 0.2).
- VM was replaced mid-build (service restart); toolchain restored via restore.sh (KiCad 8.0.9). exp268 build log lost in restart; board verified by DRC instead.
- NEXT: fix3c NE braid (+3V3A vias (78.8,11.62)/(79.375,16.625), SCL In2 x79.125 vertical, D7 via (79.1,15.88) + D7 B track, +3V3A B tracks, 2 dangling In2 stubs), then fix3d east D-fan (~27 items).
