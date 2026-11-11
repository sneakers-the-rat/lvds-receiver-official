#!/usr/bin/env python3
"""SH1 stage D6: C43 text to the open south strip; C37 text
rotated 90 degrees in the channel east of its own pads."""
import wx
wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp275.kicad_pcb'
board = pcbnew.LoadBoard(SRC)

def mm(v): return int(round(v * 1e6))

fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
t = fps['C43'].Reference()
t.SetPosition(pcbnew.VECTOR2I(mm(33.90), mm(37.30)))
t.SetVisible(True)
print('text C43 -> (33.90, 37.30)')
t = fps['C37'].Reference()
t.SetPosition(pcbnew.VECTOR2I(mm(42.90), mm(40.72)))
t.SetTextAngle(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
t.SetVisible(True)
print('text C37 -> (42.90, 40.72) rot90')
board.Save(SRC)
print('saved', SRC)
