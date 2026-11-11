#!/usr/bin/env python3
"""SH1 stage D5: last silk text nudges."""
import wx
wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp275.kicad_pcb'
board = pcbnew.LoadBoard(SRC)

def mm(v): return int(round(v * 1e6))

TEXTPOS = {'C43': (43.60, 45.70), 'C37': (43.00, 40.72),
           'C7': (34.40, 43.10), 'C44': (34.90, 44.60)}
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
for ref, (x, y) in TEXTPOS.items():
    t = fps[ref].Reference()
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetVisible(True)
    print('text', ref, '->', (x, y))
board.Save(SRC)
print('saved', SRC)
