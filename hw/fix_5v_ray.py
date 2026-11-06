#!/usr/bin/env python3
"""Extend +5V's U7.4 stub west on F to (68.00,14.50), clear of
the U7 fence field, so heal can start. Stub already placed by
hand_stub: (73.33,13.66)->(72.80,13.43). This script appends
segments; +5V must stay 2 groups (extension only).

Run: xvfb-run -a python3 hw/fix_5v_ray.py IN OUT
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb, repair6, repair
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM
F = pcbnew.F_Cu
IN1, IN2, B = pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
SAFETY = 0.005
W = 0.25
VD = 0.60
NET = '+5V'

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)
netobj = board.FindNet(NET)


def blockers(layers, shape):
    out = []
    for kind, n2, l2, s2, desc in items:
        if n2 == NET or kind == 'zone':
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(NET, n2, shared)
        if s2.Collide(shape, MM(need - 0.001 + SAFETY)):
            out.append((n2, desc, need))
    return out


def ngroups():
    return len(repair.compute_groups(board)[NET])


SEGS = [((72.80, 13.43), (72.80, 17.50), IN2),
        ((72.80, 17.50), (67.50, 17.50), IN2),
        ((67.50, 17.50), (67.00, 17.50), F)]
VIAS = [(72.80, 13.43), (67.50, 17.50)]
print('groups before:', ngroups())
assert ngroups() == 2
for a, b, lay in SEGS:
    sh = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])),
                              pcbnew.VECTOR2I(MM(b[0]), MM(b[1])),
                              MM(W))
    bl = blockers({lay}, sh)
    print(a, '->', b, 'blockers:', bl[:4] if bl else 'none')
    if bl:
        sys.exit(1)
for p in VIAS:
    c = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])),
                            MM(VD / 2))
    bl = blockers({F, IN1, IN2, B}, c)
    print('via', p, 'blockers:', bl[:4] if bl else 'none')
    if bl:
        sys.exit(1)
for p in VIAS:
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])))
    v.SetDrill(MM(0.30))
    v.SetWidth(MM(VD))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(F, B)
    v.SetNet(netobj)
    board.Add(v)
for a, b, lay in SEGS:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(W))
    t.SetLayer(lay)
    t.SetNet(netobj)
    board.Add(t)
print('groups after:', ngroups())
assert ngroups() == 2
repair6.save_checkpoint(board, OUT)
print('saved', OUT)
