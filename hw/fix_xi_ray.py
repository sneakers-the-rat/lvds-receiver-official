#!/usr/bin/env python3
"""XI fanout ray: extend U7.28's 0.18mm nub into a real ray so heal's
start set opens (CAP_CLK mechanism): (76.25,11.03)->(76.25,10.55) north,
then west bend ->(75.35,10.55), plus a via at the ray end if clean.
Exact-tested vs every foreign item. Asserts XI stays 2 groups (ray
only, no join claimed).

Run: xvfb-run -a python3 hw/fix_xi_ray.py IN OUT
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
F, B = pcbnew.F_Cu, pcbnew.B_Cu
SAFETY = 0.005
NET = 'XI'
W = 0.20

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)
print(f"items: {len(items)}")
xi = board.FindNet(NET)


def seg_shape(a, b, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])),
                                pcbnew.VECTOR2I(MM(b[0]), MM(b[1])),
                                MM(w))


def blockers(net, layers, shape):
    out = []
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        if s2.Collide(shape, MM(need - 0.001 + SAFETY)):
            out.append((n2, desc, need))
    return out


def ngroups(board):
    return len(repair.compute_groups(board)[NET])


g0 = ngroups(board)
segs = [((76.25, 11.03), (76.25, 10.55)), ((76.25, 10.55), (75.85, 10.55))]
for a, b in segs:
    bl = blockers(NET, {F}, seg_shape(a, b, W))
    print('ray', a, '->', b, 'BLOCKERS:', bl[:5] if bl else 'none')
    if bl:
        print('ABORT: ray segment blocked')
        sys.exit(1)
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(W))
    t.SetLayer(F)
    t.SetNet(xi)
    board.Add(t)

for vx, vy in [(76.25, 10.55), (75.85, 10.55)]:
    c = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(vx), MM(vy)), MM(0.30))
    bl = blockers(NET, {F, pcbnew.In1_Cu, pcbnew.In2_Cu, B}, c)
    print(f'ray via ({vx},{vy}) d=0.60 BLOCKERS:', bl[:5] if bl else 'none')
    if not bl:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy)))
        v.SetDrill(MM(0.30))
        v.SetWidth(MM(0.60))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(F, B)
        v.SetNet(xi)
        board.Add(v)
        break

g1 = ngroups(board)
print('XI groups before/after ray:', g0, g1)
assert g1 == g0 == 2
repair6.save_checkpoint(board, OUT)
print('saved', OUT)
