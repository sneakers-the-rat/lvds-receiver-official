#!/usr/bin/env python3
"""Stage 2b: placement corrections for the T1 swap district.

- T1 shifts 1.6 mm east (west pads clear D10.2 by 2.5 mm instead of
  0.85; also relieves the T1 x D11 courtyard overlap).
- D11 shifts west so its courtyard clears T1's; its HV_OVP2 stub is
  re-laid at x=14.6 onto the moved pad.
- Ladder re-placed to the v4 layout (docs/12 flow, east column):
  C52/D12 row A, D13/C53 row B, C54 east of D13, D14/D15 on the
  y=-5 row where M3 runs straight and HV_RAW exits south to the
  original board's In2 hop vias.
"""
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

move('T1', 34.5, -31.4)
move('D11', 15.9, -20.25)
move('C52', 45.5, -16.5)
move('D12', 39.5, -16.5)
move('D13', 39.5, -11.0)
move('C53', 33.0, -11.0)
move('C54', 45.5, -11.0, rot=0)
move('D14', 45.5, -5.0, rot=180)
move('D15', 38.0, -5.0, rot=0)

# D11 HV_OVP2 stub re-lay: rip (15.1,-20.25)-(15.1,-21.75), add at 14.6
victims = []
for t in board.GetTracks():
    if t.GetNetname() != 'HV_OVP2':
        continue
    a, b = t.GetStart(), t.GetEnd()
    pts = {(round(a.x / 1e6, 2), round(a.y / 1e6, 2)),
           (round(b.x / 1e6, 2), round(b.y / 1e6, 2))}
    if pts == {(15.1, -20.25), (15.1, -21.75)}:
        victims.append(t)
print('OVP2 stub victims:', len(victims))
for t in victims:
    board.Remove(t)
net = board.FindNet('HV_OVP2')
for (x1, y1, x2, y2) in [(14.6, -20.25, 14.6, -21.75), (14.6, -21.75, 15.1, -21.75)]:
    tr = pcbnew.PCB_TRACK(board)
    tr.SetStart(VECTOR2I(FromMM(x1), FromMM(y1)))
    tr.SetEnd(VECTOR2I(FromMM(x2), FromMM(y2)))
    tr.SetWidth(FromMM(0.4))
    tr.SetLayer(pcbnew.F_Cu)
    tr.SetNetCode(net.GetNetCode())
    board.Add(tr)
print('OVP2 stub re-laid at x=14.6')
board.Save(BOARD)
print('saved')
