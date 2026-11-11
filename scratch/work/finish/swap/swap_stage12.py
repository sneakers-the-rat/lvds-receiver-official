#!/usr/bin/env python3
"""Stage 12: drop the HV_M2 west channel from y=-13.1 to
y=-13.35. The copied HV_RAW hop via is a grandfathered 0.8 mm
via; at the old channel height the M2 tracks passed it at
0.875/0.885 against the 1.0 HV class. At -13.35 both clear
(>=1.13). The riser into D13.1 is re-laid to match.
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
    ((34.2, -16.6), (34.2, -13.1)),
    ((34.2, -13.1), (37.5, -13.1)),
    ((37.5, -13.1), (37.5, -11.0)),
}
victims = []
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != 'HV_M2':
        continue
    a, b = P(t)
    if (a, b) in RIP or (b, a) in RIP:
        victims.append(t)
print('ripping', len(victims))
for t in victims:
    board.Remove(t)

code = board.FindNet('HV_M2').GetNetCode()
def trk(a, b):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(VECTOR2I(FromMM(a[0]), FromMM(a[1])))
    t.SetEnd(VECTOR2I(FromMM(b[0]), FromMM(b[1])))
    t.SetWidth(FromMM(0.4))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNetCode(code)
    board.Add(t)

trk((34.2, -16.6), (34.2, -13.35))
trk((34.2, -13.35), (37.5, -13.35))
trk((37.5, -13.35), (37.5, -11.0))

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD)
print('saved')
