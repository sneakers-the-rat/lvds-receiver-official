#!/usr/bin/env python3
"""Test a candidate hand-route polyline segment by segment with the
audit's need_for (same collision model as the surgery scripts).
Prints blockers per segment; exit 0 iff every segment is clear.

Usage: xvfb-run -a python3 hw/probe_path.py BOARD NET LAYER W \
    x1 y1 x2 y2 [x3 y3 ...]
LAYER is one of F, In1, In2, B. W is the track width in mm.
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM
LAYERS = {'F': pcbnew.F_Cu, 'In1': pcbnew.In1_Cu,
          'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}

board = pcbnew.LoadBoard(sys.argv[1])
net = sys.argv[2]
layer = LAYERS[sys.argv[3]]
w = float(sys.argv[4])
pts = [float(v) for v in sys.argv[5:]]
items = build_items(board)

def seg_blockers(x1, y1, x2, y2):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x1), MM(y1)),
                             pcbnew.VECTOR2I(MM(x2), MM(y2)), MM(w))
    out = []
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        if layer not in l2:
            continue
        need = need_for(net, n2, {layer})
        if s.Collide(s2, MM(need - 0.001)):
            out.append(f"{n2}:{desc}:need{need}")
    return out

ok = True
for i in range(0, len(pts) - 2, 2):
    x1, y1, x2, y2 = pts[i:i + 4]
    b = seg_blockers(x1, y1, x2, y2)
    print(f"seg ({x1},{y1})->({x2},{y2}): {'CLEAR' if not b else b}")
    ok = ok and not b
sys.exit(0 if ok else 1)
