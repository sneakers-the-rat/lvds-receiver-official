#!/usr/bin/env python3
"""Stage 2 prep: fix three ladder placements found wanting during
route planning (D15 north for the HV_RAW run, C53 west so the HV_M2
riser clears D12's GND pad, C54 flipped so HV_M1 enters from the
east and HV_M3 leaves westward), then dump the surviving stub ends
of +5V / FLY_PRI / HV_RAW inside the district box."""
import wx
_app = wx.App(False)
import pcbnew
from pcbnew import VECTOR2I, FromMM

BOARD = 'hw/pdlvds_rx.exp274.kicad_pcb'
board = pcbnew.LoadBoard(BOARD)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

def move(ref, x, y, rot=None):
    fp = fps[ref]
    fp.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
    if rot is not None:
        fp.SetOrientationDegrees(rot)
    fp.Reference().SetPosition(VECTOR2I(FromMM(x), FromMM(y - 2.6)))
    fp.Value().SetPosition(VECTOR2I(FromMM(x), FromMM(y + 2.6)))
    print(ref, '->', x, y, 'rot', fp.GetOrientationDegrees())
    for pad in fp.Pads():
        c = pad.GetPosition()
        print('   ', pad.GetNumber(), pad.GetNetname(),
              round(c.x / 1e6, 2), round(c.y / 1e6, 2))

move('D15', 32.0, -16.5)
move('C53', 35.5, -12.5)
move('C54', 40.5, -21.5, rot=180)
board.Save(BOARD)

print('--- surviving stubs in district (x 8..58, y -46..-2) ---')
for t in board.GetTracks():
    if t.GetNetname() not in ('+5V', 'FLY_PRI', 'HV_RAW'):
        continue
    a, b = t.GetStart(), t.GetEnd()
    pts = [(a.x / 1e6, a.y / 1e6), (b.x / 1e6, b.y / 1e6)]
    if any(8 <= x <= 58 and -46 <= y <= -2 for x, y in pts):
        kind = 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk'
        print(t.GetNetname(), kind, t.GetLayerName(),
              [(round(x, 2), round(y, 2)) for x, y in pts],
              'w', round(t.GetWidth() / 1e6, 2))
