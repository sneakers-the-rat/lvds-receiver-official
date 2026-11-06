#!/usr/bin/env python3
"""Dump pads/tracks/vias whose position falls in a box.

Usage: probe_box.py BOARD X0 X1 Y0 Y1 [NET]
Layer names use the true KiCad ids: F=0, In1=1, In2=2, B=31.
(Pads print their position; tracks print both endpoints when
either endpoint is in the box.)
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

BOARD = sys.argv[1]
X0, X1, Y0, Y1 = (float(v) for v in sys.argv[2:6])
NETF = sys.argv[6] if len(sys.argv) > 6 else None
LN = {0: 'F', 1: 'In1', 2: 'In2', 31: 'B'}
board = pcbnew.LoadBoard(BOARD)

def inbox(x, y):
    return X0 <= x <= X1 and Y0 <= y <= Y1

for fp in board.GetFootprints():
    for pad in fp.Pads():
        p = pcbnew.ToMM(pad.GetPosition())
        if not inbox(p[0], p[1]):
            continue
        net = pad.GetNetname()
        if NETF and net != NETF:
            continue
        sz = pcbnew.ToMM(pad.GetSize())
        layers = [LN.get(l, str(l)) for l in
                  (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
                  if pad.IsOnLayer(l)]
        print(f"PAD {fp.GetReference()}.{pad.GetNumber()} {net} "
              f"({p[0]:.2f},{p[1]:.2f}) {sz[0]:.2f}x{sz[1]:.2f} L={layers}")
for t in board.GetTracks():
    net = t.GetNetname()
    if NETF and net != NETF:
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition())
        if inbox(p[0], p[1]):
            print(f"VIA {net} ({p[0]:.2f},{p[1]:.2f}) "
                  f"d={pcbnew.ToMM(t.GetWidth()):.2f}")
    else:
        a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
        if inbox(a[0], a[1]) or inbox(b[0], b[1]):
            print(f"TRK {net} L{LN.get(t.GetLayer(), t.GetLayer())} "
                  f"({a[0]:.2f},{a[1]:.2f})->({b[0]:.2f},{b[1]:.2f}) "
                  f"w={pcbnew.ToMM(t.GetWidth()):.2f}")
