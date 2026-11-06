#!/usr/bin/env python3
"""Connect VCAP2 (U6.71 bare pad -> C18.1 group with stub).
F route: south exit (90.25,5.40)->(90.25,6.40); east to
(93.35,6.40); north to (93.35,-3.20); east into the stub
end (94.03,-3.20). All exact-tested; groups 2 -> 1.

Run: xvfb-run -a python3 hw/fix_vcap2.py IN OUT
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
W = 0.20
VD = 0.60
NET = 'VCAP2'

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


SEGS = [((90.25, 5.40), (90.25, 6.10), F),
        ((90.25, 6.10), (93.35, 6.10), B),
        ((93.35, 6.10), (93.35, -3.20), B),
        ((93.35, -3.20), (94.03, -3.20), F)]
VIAS = [(90.25, 6.10), (93.35, -3.20)]
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
assert ngroups() == 1
repair6.save_checkpoint(board, OUT)
print('saved', OUT)
