#!/usr/bin/env python3
"""Connect ULPI_D5's lone pad U7.19 (knot member).

U7.19's east exit is walled by ULPI_D4's escape bend
(79.15,14.30)->(79.22,14.98)->(79.55,15.05)->via(80.12,15.38).
Mechanism: relay D4 (victim repaid in-pass) -- rip its bend,
run F (79.15,14.30)->(79.90,14.45), dive at (79.90,14.45),
In2 hop onto D4's old via (80.12,15.38). Then D5 runs the freed
latitude: F (78.88,14.75)->(79.30,15.15)->(80.88,15.12), the NW
tip of D5's web. Groups asserted: D4 stays 1, D5 goes 2 -> 1.

Run: xvfb-run -a python3 hw/fix_d5.py IN OUT
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
IN2 = pcbnew.In2_Cu
SAFETY = 0.005
W = 0.20
VD = 0.60

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)


def seg_shape(a, b, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])),
                                pcbnew.VECTOR2I(MM(b[0]), MM(b[1])),
                                MM(w))


def blockers(items, net, layers, shape):
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


def add_track(a, b, layer, net, w=W):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    return t


assert ngroups('ULPI_D5') == 2 and ngroups('ULPI_D4') == 1

# --- stage 1: test D4 relay pieces against the current board
items = build_items(board)
RELAY_F = [((79.15, 14.30), (79.55, 14.60)), ((79.55, 14.60), (79.90, 14.45))]
for a, b in RELAY_F:
    bl = blockers(items, 'ULPI_D4', {F}, seg_shape(a, b, W))
    print('D4 relay F', a, '->', b, 'blockers:', bl[:4] if bl else 'none')
    if bl:
        sys.exit(1)
c = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(79.90), MM(14.45)), MM(VD / 2))
bl = blockers(items, 'ULPI_D4', {F, pcbnew.In1_Cu, IN2, B}, c)
print('D4 relay via blockers:', bl[:4] if bl else 'none')
if bl:
    sys.exit(1)
bl = blockers(items, 'ULPI_D4', {IN2}, seg_shape((79.90, 14.45), (80.12, 15.38), W))
print('D4 relay In2 hop blockers:', bl[:4] if bl else 'none')
if bl:
    sys.exit(1)

# --- stage 2: rip D4's bend, lay the relay
RIP = [{(79.15, 14.30), (79.22, 14.98)}, {(79.22, 14.98), (79.55, 15.05)},
       {(79.55, 15.05), (80.12, 15.38)}]
ripped = 0
for t in list(board.GetTracks()):
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != 'ULPI_D4' \
            or t.GetLayer() != F:
        continue
    a = (round(pcbnew.ToMM(t.GetStart().x), 2), round(pcbnew.ToMM(t.GetStart().y), 2))
    b = (round(pcbnew.ToMM(t.GetEnd().x), 2), round(pcbnew.ToMM(t.GetEnd().y), 2))
    if {a, b} in RIP:
        board.Remove(t)
        ripped += 1
print('D4 bend segments ripped:', ripped)
assert ripped == 3
for a, b in RELAY_F:
    add_track(a, b, F, 'ULPI_D4')
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(79.90), MM(14.45)))
v.SetDrill(MM(0.30))
v.SetWidth(MM(VD))
v.SetViaType(pcbnew.VIATYPE_THROUGH)
v.SetLayerPair(F, B)
v.SetNet(board.FindNet('ULPI_D4'))
board.Add(v)
add_track((79.90, 14.45), (80.12, 15.38), IN2, 'ULPI_D4')
assert ngroups('ULPI_D4') == 1, 'D4 partition changed by relay!'
print('D4 relayed, still 1 group')

# --- stage 3: D5 run, tested against the updated board
items = build_items(board)
D5RUN = [((78.88, 14.75), (79.30, 15.15)), ((79.30, 15.15), (80.88, 15.12))]
for a, b in D5RUN:
    bl = blockers(items, 'ULPI_D5', {F}, seg_shape(a, b, W))
    print('D5 run', a, '->', b, 'blockers:', bl[:4] if bl else 'none')
    if bl:
        print('ABORT (D4 relay already applied in memory only; not saved)')
        sys.exit(1)
for a, b in D5RUN:
    add_track(a, b, F, 'ULPI_D5')
assert ngroups('ULPI_D5') == 1, 'D5 join failed'
print('D5 connected')
repair6.save_checkpoint(board, OUT)
print('saved', OUT)
