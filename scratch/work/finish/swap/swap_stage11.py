#!/usr/bin/env python3
"""Stage 11: move T1.3's GND via off the FLY_PRI In2 column.
The via at (26.1,-28.6) sat on FLY_PRI's buried vertical run
(x=26.0). South leg and via move east to x=26.8 (0.35 clear of
the buried run, 1.8+ clear of T1's shifted pads).
"""
import wx
_app = wx.App(False)
import pcbnew
from pcbnew import VECTOR2I, FromMM

BOARD = 'hw/pdlvds_rx.exp274.kicad_pcb'
board = pcbnew.LoadBoard(BOARD)

def P(t):
    a, b = t.GetStart(), t.GetEnd()
    return ((round(a.x / 1e6, 2), round(a.y / 1e6, 2)),
            (round(b.x / 1e6, 2), round(b.y / 1e6, 2)))

RIP = {
    ('GND', ((23.1, -32.9), (26.1, -32.9))),
    ('GND', ((26.1, -32.9), (26.1, -28.6))),
}
victims = []
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        c = t.GetPosition()
        if t.GetNetname() == 'GND' and (round(c.x / 1e6, 2), round(c.y / 1e6, 2)) == (26.1, -28.6):
            victims.append(t)
    else:
        a, b = P(t)
        if (t.GetNetname(), (a, b)) in RIP or (t.GetNetname(), (b, a)) in RIP:
            victims.append(t)
print('ripping', len(victims))
for t in victims:
    board.Remove(t)

code = board.FindNet('GND').GetNetCode()
def trk(a, b):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(VECTOR2I(FromMM(a[0]), FromMM(a[1])))
    t.SetEnd(VECTOR2I(FromMM(b[0]), FromMM(b[1])))
    t.SetWidth(FromMM(0.4))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNetCode(code)
    board.Add(t)

trk((23.1, -32.9), (26.8, -32.9))
trk((26.8, -32.9), (26.8, -28.6))
v = pcbnew.PCB_VIA(board)
v.SetPosition(VECTOR2I(FromMM(26.8), FromMM(-28.6)))
v.SetWidth(FromMM(0.5))
v.SetDrill(FromMM(0.3))
v.SetViaType(pcbnew.VIATYPE_THROUGH)
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNetCode(code)
board.Add(v)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD)
print('saved')
