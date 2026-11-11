#!/usr/bin/env python3
"""SH1 stage D2 (fresh load): reposition the silk texts."""
import wx
wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp275.kicad_pcb'
board = pcbnew.LoadBoard(SRC)

def mm(v): return int(round(v * 1e6))

TEXTPOS = {
    'SH1': (21.05, 37.25),
    'CL1': (22.20, 28.20), 'CL2': (29.90, 28.30),
    'CL3': (13.30, 43.30), 'CL5': (32.70, 30.80),
    'CL4': (9.30, 36.60),
    'R8': (27.50, 34.60), 'C7': (35.50, 44.40),
    'C44': (35.80, 45.90), 'C2': (36.10, 47.40),
    'C37': (41.40, 40.10), 'C43': (42.40, 43.30),
}
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
for ref, (x, y) in TEXTPOS.items():
    t = fps[ref].Reference()
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetVisible(True)
    print('text', ref, '->', (x, y))
board.Save(SRC)
print('saved', SRC)
