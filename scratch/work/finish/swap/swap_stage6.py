#!/usr/bin/env python3
"""Stage 6: rip the dangling HV_OVP2 remnant at x=14.6 (left over
from the stage-2b re-lay; both its neighbours are gone). Refill
and save. The two zone-vs-zone DRC items are a demonstrated
scripted-refill artifact (control: refilling the untouched
canonical board reproduces them exactly) and are dispositioned
as such in the pass record, not fixed here.
"""
import wx
_app = wx.App(False)
import pcbnew

BOARD = 'hw/pdlvds_rx.exp274.kicad_pcb'
board = pcbnew.LoadBoard(BOARD)

victims = []
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != 'HV_OVP2':
        continue
    a, b = t.GetStart(), t.GetEnd()
    pa = (round(a.x / 1e6, 2), round(a.y / 1e6, 2))
    pb = (round(b.x / 1e6, 2), round(b.y / 1e6, 2))
    if pa[0] == 14.6 or pb[0] == 14.6:
        victims.append(t)
        print('rip', pa, pb)
for t in victims:
    board.Remove(t)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD)
print('saved; ripped', len(victims))
