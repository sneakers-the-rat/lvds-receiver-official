#!/usr/bin/env python3
"""SH1 stage F2: restore the can/clip refdes positions that the
stage-F footprint reload reset to library defaults (positions as
settled by stages D2-D6)."""
import wx
wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp275.kicad_pcb'
board = pcbnew.LoadBoard(SRC)

def mm(v): return int(round(v * 1e6))

TEXTPOS = {'SH1': (21.05, 31.90), 'CL1': (21.30, 28.20),
           'CL2': (30.30, 28.60), 'CL3': (13.30, 43.30),
           'CL4': (12.20, 35.60), 'CL5': (32.70, 30.80)}
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
for ref, (x, y) in TEXTPOS.items():
    t = fps[ref].Reference()
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetVisible(True)
    print('text', ref, '->', (x, y))
board.Save(SRC)
print('saved', SRC)
