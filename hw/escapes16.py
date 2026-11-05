#!/usr/bin/env python3
"""Escape + join surgery batch 16 -- HV_RAW all-F north route.
The APD_K via (41.12,-4.38, 0.8 dia) exclusion (r=1.6 for a
0.4 track at the 1.0 class) plus APD_K's F island track fence
every south/west approach; the north crossing at y~-2.7 (1.75
from the via centre) is open, and from (39.9,-5.6) the island
stub joins on F with no via at all.
Board-agnostic: xvfb-run -a python3 hw/escapes16.py <src> <out>
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
MMf = pcbnew.FromMM
MMt = pcbnew.ToMM
SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)

def seg_blocked(net, x1, y1, x2, y2, w, layer):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x1), MMf(y1)),
                             pcbnew.VECTOR2I(MMf(x2), MMf(y2)),
                             MMf(w))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        if layer not in l2:
            continue
        need = need_for(net, n2, {layer})
        if s.Collide(s2, MMf(need - 0.001)):
            return f'{n2} {desc}'
    return None

def add_track(net, x1, y1, x2, y2, w=0.25, layer=pcbnew.F_Cu):
    bad = seg_blocked(net, x1, y1, x2, y2, w, layer)
    assert not bad, f'{net} seg ({x1},{y1})->({x2},{y2}): {bad}'
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MMf(x1), MMf(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MMf(x2), MMf(y2)))
    t.SetWidth(MMf(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    print(f'  {net}: ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) L{layer}')


def rip_seg(net, x1, y1, x2, y2):
    for t in list(board.GetTracks()):
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != net:
            continue
        a = (MMt(t.GetStart().x), MMt(t.GetStart().y))
        b = (MMt(t.GetEnd().x), MMt(t.GetEnd().y))
        for (p, q) in ((a, b), (b, a)):
            if (abs(p[0] - x1) < 0.6 and abs(p[1] - y1) < 0.6
                    and abs(q[0] - x2) < 0.6 and abs(q[1] - y2) < 0.6):
                board.Remove(t)
                print(f'  rip {net} ({a[0]:.2f},{a[1]:.2f})->'
                      f'({b[0]:.2f},{b[1]:.2f})')
                return
    print(f'  rip {net}: NOT FOUND')

rip_seg('HV_FBX', 39.16, -2.4, 38.75, -0.9)
items = build_items(board)

pts = [(41.60, -2.70), (40.40, -2.75), (39.30, -3.60),
       (39.30, -5.20), (39.90, -5.60), (39.30, -7.50),
       (39.53, -9.80)]
try:
    for (a, b) in zip(pts, pts[1:]):
        add_track('HV_RAW', a[0], a[1], b[0], b[1], w=0.4)
    print('  [HV_RAW north route OK]')
except AssertionError as exc:
    print(f'  [HV_RAW north route REFUSED: {exc}]')

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')
