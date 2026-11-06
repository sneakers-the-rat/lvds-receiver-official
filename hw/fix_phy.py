#!/usr/bin/env python3
"""Connect PHY_1V8A (C23.1 + U7.29) and PHY_1V8's U7.15<->C22.1
chain. U7.26 is NOT attempted: its north field is tiled by
CDR_DATP's via (76.88,10.62) + ULPI_CK's staircase + the pad
row (knot-class; mechanisms: CDR pair relay / U7 move).

PHY_1V8A: F ray (75.75,11.12)->(75.75,10.75); via; B west
(75.75,10.75)->(75.10,10.75), jog south around +3V3A's via
(74.12,10.38): (75.10,10.75)->(74.85,11.55)->(73.40,11.55)
->(73.15,10.75); B west to (65.70,10.75); B south to
(65.70,17.20); via; F (65.70,17.20)->(65.70,17.90)->
(65.22,17.90)->(65.22,18.10) into C23.1.
PHY_1V8: F ray (77.25,16.88)->(77.25,18.30); west run
y=18.30 to (69.70,18.30); south to (69.70,19.40); east to
(69.22,19.40); south into C22.1 (69.22,19.60).
Groups: A 2 -> 1, 1V8 3 -> 2, or not saved.

Run: xvfb-run -a python3 hw/fix_phy.py IN OUT
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
IN1, IN2 = pcbnew.In1_Cu, pcbnew.In2_Cu
SAFETY = 0.005
W = 0.20
VD = 0.60
ALL = {F, IN1, IN2, B}

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)
print(f"items: {len(items)}")


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


def ngroups(net):
    return len(repair.compute_groups(board)[net])


def add_track(net, a, b, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(W))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    return t


def add_via(net, p):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])))
    v.SetDrill(MM(0.30))
    v.SetWidth(MM(VD))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(F, B)
    v.SetNet(board.FindNet(net))
    board.Add(v)
    return v


def test_seg(net, a, b, layer):
    bl = blockers(net, {layer}, seg_shape(a, b, W))
    print(net, a, '->', b, 'blockers:', bl[:4] if bl else 'none')
    if bl:
        sys.exit(1)


def test_via(net, p):
    c = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])),
                            MM(VD / 2))
    bl = blockers(net, ALL, c)
    print(net, 'via', p, 'blockers:', bl[:4] if bl else 'none')
    if bl:
        sys.exit(1)


def rip(net, a, b):
    n = 0
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net:
            continue
        s = (round(pcbnew.ToMM(t.GetStart().x), 2),
             round(pcbnew.ToMM(t.GetStart().y), 2))
        e = (round(pcbnew.ToMM(t.GetEnd().x), 2),
             round(pcbnew.ToMM(t.GetEnd().y), 2))
        if {s, e} == {a, b}:
            board.Remove(t)
            n += 1
    print(f'ripped {net} {a}->{b}: {n}')
    assert n == 1


def add_via2(net, p):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])))
    v.SetDrill(MM(0.30))
    v.SetWidth(MM(VD))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(F, B)
    v.SetNet(board.FindNet(net))
    board.Add(v)
    return v


def test_via2(net, p):
    c = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])),
                            MM(VD / 2))
    bl = blockers(net, {F, IN1, IN2, B}, c)
    print(net, 'via', p, 'blockers:', bl[:4] if bl else 'none')
    if bl:
        sys.exit(1)


A = 'PHY_1V8A'
V = 'PHY_1V8'
print('groups before:', ngroups(V), ngroups(A))
assert ngroups(V) == 3 and ngroups(A) == 2
assert ngroups('ULPI_CK') == 1

VA1 = (75.75, 10.75)
VA2 = (65.70, 17.20)
ASEGS = []
VSEGS = [(V, (77.25, 16.88), (77.38, 17.60), F),
         (V, (77.38, 17.60), (77.38, 18.30), F),
         (V, (77.38, 18.30), (69.70, 18.30), F),
         (V, (69.70, 18.30), (69.70, 19.40), F),
         (V, (69.70, 19.40), (69.22, 19.40), F),
         (V, (69.22, 19.40), (69.22, 19.60), F)]
CKV = (76.62, 17.30)
for net, a, b, lay in ASEGS:
    test_seg(net, a, b, lay)
test_seg('ULPI_CK', (76.62, 17.30), (77.62, 17.62), IN2)
test_via2('ULPI_CK', CKV)

# ULPI_CK relay: rip its F diagonal pair, dive at CKV, In2 hop
# onto its own In2 vertical (77.62,17.62)-(77.62,17.88).
rip('ULPI_CK', (76.75, 17.19), (77.12, 17.38))
rip('ULPI_CK', (77.12, 17.38), (77.38, 17.62))
rip('ULPI_CK', (77.38, 17.62), (77.62, 17.88))
add_via2('ULPI_CK', CKV)
t = pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(MM(76.62), MM(17.30)))
t.SetEnd(pcbnew.VECTOR2I(MM(77.62), MM(17.62)))
t.SetWidth(MM(W))
t.SetLayer(IN2)
t.SetNet(board.FindNet('ULPI_CK'))
board.Add(t)
assert ngroups('ULPI_CK') == 1, 'CK relay broke CK'
items = build_items(board)
print(f"items refreshed: {len(items)}")

for net, a, b, lay in VSEGS:
    test_seg(net, a, b, lay)
for net, a, b, lay in VSEGS:
    add_track(net, a, b, lay)

print('groups after:', ngroups(V), ngroups(A))
assert ngroups(V) == 2 and ngroups(A) == 2, 'join failed'
repair6.save_checkpoint(board, OUT)
print('saved', OUT)
