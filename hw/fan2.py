#!/usr/bin/env python3
"""Measured escape fan: for each named pad, cast 16 rays from the
pad CENTRE on F.Cu against every foreign item (pads, tracks, vias
-- build_items shapes, zones excluded). Each ray grows in 0.25mm
steps to 6mm; report the free length (last clean step) and the
first blocker (net, desc, bbox centre). Also scan a ring of via
sites (r = 1.2..3.0mm, 16 angles) and report the clear ones.
Usage: xvfb-run -a python3 hw/fan2.py <board> REF.PIN [...]
"""
import math
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MMf = pcbnew.FromMM
MMt = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])
items = build_items(board)
pads = {}
for fp in board.GetFootprints():
    for p in fp.Pads():
        pads[f'{fp.GetReference()}.{p.GetNumber()}'] = (
            MMt(p.GetPosition().x), MMt(p.GetPosition().y),
            p.GetNetname())

def centre(s2):
    try:
        bb = s2.GetBoundingBox()
        return (MMt(bb.GetCenter().x), MMt(bb.GetCenter().y))
    except Exception:
        return (float('nan'), float('nan'))

def seg_hit(net, x1, y1, x2, y2, w=0.25):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x1), MMf(y1)),
                             pcbnew.VECTOR2I(MMf(x2), MMf(y2)),
                             MMf(w))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        if pcbnew.F_Cu not in l2:
            continue
        need = need_for(net, n2, {pcbnew.F_Cu})
        if s.Collide(s2, MMf(need - 0.001)):
            cx, cy = centre(s2)
            return f'{n2}/{desc}@({cx:.1f},{cy:.1f})'
    return None

def disc_hit(net, x, y):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x), MMf(y)),
                             pcbnew.VECTOR2I(MMf(x), MMf(y)),
                             MMf(0.6))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        need = need_for(net, n2, l2)
        if s.Collide(s2, MMf(need - 0.001)):
            cx, cy = centre(s2)
            return f'{n2}/{desc}@({cx:.1f},{cy:.1f})'
    return None

for name in sys.argv[2:]:
    cx, cy, net = pads[name]
    print(f'== {name} ({net}) at ({cx:.2f},{cy:.2f}) ==')
    for k in range(16):
        ang = math.radians(k * 22.5)
        dx, dy = math.cos(ang), math.sin(ang)
        free, blocker = 0.0, None
        for step in range(1, 25):
            L = step * 0.25
            hit = seg_hit(net, cx, cy, cx + dx * L, cy + dy * L)
            if hit:
                blocker = hit
                break
            free = L
        tag = f'blocked by {blocker}' if blocker else 'FREE>=6'
        print(f'  {k * 22.5:6.1f}deg: free {free:4.2f}  {tag}')
    vias = []
    for r in (1.2, 1.8, 2.4, 3.0):
        for k in range(16):
            ang = math.radians(k * 22.5)
            x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
            if not disc_hit(net, x, y):
                vias.append(f'({x:.1f},{y:.1f})')
    print(f'  clear via sites: {" ".join(vias) if vias else "NONE"}')
