#!/usr/bin/env python3
"""Dump every copper item whose bounding box comes within D mm of a
point: pads, tracks, vias with net, layer, bbox.
Usage: xvfb-run -a python3 hw/probe_point.py <board> X Y [D]
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

MMt = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])
X, Y = float(sys.argv[2]), float(sys.argv[3])
D = float(sys.argv[4]) if len(sys.argv) > 4 else 2.5
LN = {0: 'F', 2: 'In2', 31: 'B'}
for fp in board.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        x0, x1 = MMt(bb.GetX()), MMt(bb.GetRight())
        y0, y1 = MMt(bb.GetY()), MMt(bb.GetBottom())
        if x0 - D <= X <= x1 + D and y0 - D <= Y <= y1 + D:
            print(f'PAD {fp.GetReference()}.{p.GetNumber()} '
                  f'({p.GetNetname()}) bbox x[{x0:.2f},{x1:.2f}] '
                  f'y[{y0:.2f},{y1:.2f}]')
for t in board.GetTracks():
    bb = t.GetBoundingBox()
    x0, x1 = MMt(bb.GetX()), MMt(bb.GetRight())
    y0, y1 = MMt(bb.GetY()), MMt(bb.GetBottom())
    if x0 - D <= X <= x1 + D and y0 - D <= Y <= y1 + D:
        kind = 'VIA' if t.Type() == pcbnew.PCB_VIA_T else 'TRK'
        print(f'{kind} {t.GetNetname()} L{t.GetLayer()} '
              f'({MMt(t.GetStart().x):.2f},{MMt(t.GetStart().y):.2f})'
              f'->({MMt(t.GetEnd().x):.2f},{MMt(t.GetEnd().y):.2f}) '
              f'w={MMt(t.GetWidth()):.2f}')
