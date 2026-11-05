#!/usr/bin/env python3
"""Restore ULPI_CK's F->In2 junction via at (77.62,17.88).

bridge's +3V3A join on exp99 ripped this via (one of its 2
victims), splitting CK into [U7.14 + F jog] and the main group
whose In2 staircase starts at exactly (77.62,17.88). The site
shape-tests clean on exp101. Via only; no other change.

Run: xvfb-run -a python3 hw/fix_ckvia.py IN OUT
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(77.62), pcbnew.FromMM(17.88)))
v.SetWidth(pcbnew.FromMM(0.6))
v.SetDrill(pcbnew.FromMM(0.3))
v.SetNet(board.FindNet('ULPI_CK'))
board.Add(v)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'placed ULPI_CK via (77.62,17.88) -> {OUT}')
