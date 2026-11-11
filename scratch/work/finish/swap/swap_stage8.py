#!/usr/bin/env python3
"""Stage 8: bridge the APD_A escape at D1 pad 3. The corrected
narrower pad (rect x[6.65,7.35]) no longer bridges the vertical
stub at (7.15,41.1) and the east run starting at (7.8,41.1) the
way the old 1.30-wide pad did; one 0.2 segment joins them.
"""
import wx
_app = wx.App(False)
import pcbnew
from pcbnew import VECTOR2I, FromMM

BOARD = 'hw/pdlvds_rx.exp274.kicad_pcb'
board = pcbnew.LoadBoard(BOARD)
code = board.FindNet('APD_A').GetNetCode()
t = pcbnew.PCB_TRACK(board)
t.SetStart(VECTOR2I(FromMM(7.15), FromMM(41.1)))
t.SetEnd(VECTOR2I(FromMM(7.8), FromMM(41.1)))
t.SetWidth(FromMM(0.2))
t.SetLayer(pcbnew.F_Cu)
t.SetNetCode(code)
board.Add(t)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD)
print('saved')
