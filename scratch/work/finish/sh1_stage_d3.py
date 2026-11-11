#!/usr/bin/env python3
"""SH1 stage D3: second round of silk text placement."""
import wx
wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp275.kicad_pcb'
board = pcbnew.LoadBoard(SRC)

def mm(v): return int(round(v * 1e6))

TEXTPOS = {
    'CL2': (30.30, 28.60), 'CL1': (21.30, 28.20),
    'C2': (35.50, 48.20), 'U3': (34.60, 47.11),
    'C37': (42.60, 40.60), 'CL4': (12.20, 35.60),
    'C5': (28.90, 33.90), 'SH1': (21.05, 31.90),
    'C43': (42.70, 42.20), 'U2': (29.70, 31.40),
    'C44': (35.30, 44.90),
}
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
for ref, (x, y) in TEXTPOS.items():
    t = fps[ref].Reference()
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetVisible(True)
    print('text', ref, '->', (x, y))
board.Save(SRC)
print('saved', SRC)
