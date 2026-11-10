# bn status — inherit bm exp270, finish repair (220), build USB_RST (221)

## Inherited (verified first-hand)
- Local tip b4989160 (bm fix3c) + bm final status commit d8fff19b.
  PUSHED to GitHub origin/main = d8fff19b (verified via ls-remote
  against github.com, ff-only merge in clean worktree).
- Board hw/pdlvds_rx.exp270.kicad_pcb: DRC 32, check_pcb unconnected
  = USB_RST only. bm referee files: scratch/work/bm/drc270_items.txt.
- The 32 = 4 J1 copper_edge (standing) + 1 UNCONN (USB_RST) + 27 in
  ONE district: the east D-fan NE of U7 (x79-81.6, y10.9-15.6) —
  bm's planned "fix3d". C48/C19 local included.

## bn_fix1 design (exp271) — east D-fan re-fan at pitch
- Move C48 +0.8E (decap, movable; frees D2/D3/D6 via zone). Re-lay
  its +3V3D F feed from via (81.625,10.9) (also fixes feed vs
  C19.1 NRST pad knife -0.001).
- D0 F middle re-lay west (D0/D1 mutual clearance).
- D1 F corner re-lay via (79.7,12.35).
- D2 via -> (80.05,12.9) (was hole-clr vs C19.1); F feed + In2 head.
- D4 In2 head re-lay east (D3 via fence).
- D5 via -> (80.35,15.15); F feed + In2 head re-lay.
- D6 via -> (80.7,14.6) d0.5 (was d0.6 vs C48.1 + +3V3D B highway);
  F fan re-lay south-east arc; In2 head re-lay.
- D3 via stays (80.15,13.7) once C48 moves.

## Then
- Bank pass 220 (commit_pass.py) at DRC 4 J1, courtyard 0, nets 1.
- USB_RST build per task brief (bi dive, arrival at legal d0.50),
  re-gated on exp271 geometry. Bank pass 221 at nets 0. STOP.
