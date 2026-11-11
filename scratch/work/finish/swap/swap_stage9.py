#!/usr/bin/env python3
"""Stage 9: re-feed D13.1. The stage-7 diagonal from the HV_M2
via (34.2,-16.6) to (37.5,-12.6) grazed D12's GND pad (0.74 vs
the 1.0 class in check_pcb's census). Replace it with a north
run at x=34.2 -- which passes through C53.1's pad, same net --
then east along the y=-13.1 channel into the existing riser.
"""
import wx
_app = wx.App(False)
import pcbnew
from pcbnew import VECTOR2I, FromMM

BOARD = 'hw/pdlvds_rx.exp274.kicad_pcb'
board = pcbnew.LoadBoard(BOARD)

victims = []
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != 'HV_M2':
        continue
    a, b = t.GetStart(), t.GetEnd()
    pa = (round(a.x / 1e6, 2), round(a.y / 1e6, 2))
    pb = (round(b.x / 1e6, 2), round(b.y / 1e6, 2))
    if {pa, pb} == {(34.2, -16.6), (37.5, -12.6)}:
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

trk((34.2, -16.6), (34.2, -13.1))
trk((34.2, -13.1), (37.5, -13.1))

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD)
print('saved')
