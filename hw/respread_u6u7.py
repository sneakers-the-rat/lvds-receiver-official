#!/usr/bin/env python3
"""Respread prototype: relocate U6 (STM32) + U7 (USB3300) so the ULPI
pinout faces its pairing, following move_cluster.py semantics: move
footprints, rip ALL tracks/vias of nets touching moved pads plus
bystander nets with copper within RIP_R of a new pad; GND copper is
kept (zones/pours are not tracks). Affected nets are left pad-only
for heal/thread repair in the new geometry.

Baseline geometry (exp41, pad centres from companions_respread.py):
  U6 ULPI pads on S edge (D1 71.8,43.7 / D2 72.2,43.7 / D3 83.2,43.7 /
  D4 83.8,43.7 / RST 68.8,43.7), E edge (D5 86.7,41.8 / D6 86.7,41.2),
  W edge (NXT 65.3,38.2 / STP 65.3,36.8).
  U7 ULPI pads on E edge (88.4,-22.2..-19.8), N edge (NXT/STP/RST
  y=-18.6). Pad-to-pad haul ~66 mm, across the whole board.

Moves:
  U6 (76,33) -> (76,-4): pure N translation into the open mid band.
  U6-exclusive local ring translates with it (C16,C17,C19,C48,C49,
  R15,R16,TP2,TP3); C47 and C18 get hand spots (their rigid-translate
  targets land inside U5 / the LED row).
  U7 (86,-21) -> (76,14): directly S of U6's new position, unrotated;
  its ULPI data edge (E) then sits ~6-11 mm from U6's S-edge data pads.
  U7 ring placed around it: X1 (84,14) rot 90 (E flank), C20 (80,20.5),
  C21 (88,20.5) crystal loads S of X1, C22 (70,20), C23 (66,18.5),
  C24 (80,19) decaps on the S/W apron.

Run: xvfb-run -a python3 hw/respread_u6u7.py [in] [out]
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

# ref -> (x, y, rot_degrees or None to keep)
MOVES = {
    # U6 + ring
    "U6":  (82, -6, None),
    "C16": (75, 9, None), "C17": (72.2, 9.5, None),
    "C19": (95, 1, None), "C48": (84, -21, None),
    "C49": (89, -9, None), "R15": (89, 1, None), "R16": (89.5, -2, None),
    "TP2": (89, -23.5, None), "TP3": (94, -18, None),
    "C47": (60, -8, None), "C18": (94, -4, None),
    # U7 + ring
    "U7":  (76, 14, None),
    "X1":  (87, 14, 90),
    "R44": (93, 7, None),
    "C20": (80, 20.5, None), "C21": (89, 23, None),
    "C22": (70, 20, None), "C23": (66, 18.5, None),
    "C24": (80, 19, None),
    "R45": (85.5, 22, None),
}
RIP_R = 2.0

def main(src="hw/pdlvds_rx.exp41.kicad_pcb",
         out="hw/pdlvds_rx.exp42.kicad_pcb"):
    board = pcbnew.LoadBoard(src)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    affected = set()
    new_pads = []
    for ref, (x, y, rot) in MOVES.items():
        fp = fps[ref]
        for pad in fp.Pads():
            if pad.GetNetname():
                affected.add(pad.GetNetname())
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        if rot is not None:
            fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            new_pads.append(pcbnew.ToMM(pad.GetPosition()))
        print(f"moved {ref} -> ({x}, {y}) rot={rot}")
    def near_new_pad(pt):
        return any((pt[0]-q[0])**2 + (pt[1]-q[1])**2 <= RIP_R**2
                   for q in new_pads)
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            pts = [pcbnew.ToMM(tr.GetPosition())]
        else:
            pts = [pcbnew.ToMM(tr.GetStart()), pcbnew.ToMM(tr.GetEnd())]
        if any(near_new_pad(p) for p in pts) and tr.GetNetname():
            affected.add(tr.GetNetname())
    affected.discard("GND")
    affected.discard("")
    print("affected nets:", sorted(affected))
    n_rip = 0
    for tr in list(board.GetTracks()):
        if tr.GetNetname() in affected:
            board.Remove(tr)
            n_rip += 1
    print(f"ripped {n_rip} tracks/vias")
    board.Save(out)
    print("saved", out)

if __name__ == "__main__":
    main(*sys.argv[1:])
