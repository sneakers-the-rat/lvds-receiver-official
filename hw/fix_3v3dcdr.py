#!/usr/bin/env python3
"""Connect +3V3D_CDR's lone pad U4.12 (queue item 6a).

The south gate fits only CF1 + CDR_LOL (record): the F underside
east run is fenced by CF2's nub, CF1's escape + via (56.12,-14.62)
and CDR_LOL's diagonal/trunk at every latitude. Mechanism: dive
at the row's south-west corner -- F diagonal from U4.12's stub end
(54.75,-15.53) to a via at (54.3,-15.0), then an In2 east run onto
the main group's In2 segment (58.62,-17.38)->(57.88,-17.38).
Candidates exact-tested in order; groups must go 2 -> 1 or the
board is not saved.

Run: xvfb-run -a python3 hw/fix_3v3dcdr.py IN OUT
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
NET = '+3V3D_CDR'
W = 0.20
VD = 0.60

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)
print(f"items: {len(items)}")
netobj = board.FindNet(NET)


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


def add_track(a, b, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(W))
    t.SetLayer(layer)
    t.SetNet(netobj)
    board.Add(t)
    return t


g0 = ngroups(board)
print('groups before:', g0)
assert g0 == 2

STUB_END = (54.75, -15.53)
VIAS = [(54.30, -15.00), (54.20, -14.80), (54.45, -14.85), (54.15, -15.15)]
chosen = None
for vxy in VIAS:
    bl = blockers(NET, {F}, seg_shape(STUB_END, vxy, W))
    if bl:
        print(f'via {vxy} stub blockers:', bl[:4])
        continue
    c = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(vxy[0]), MM(vxy[1])),
                            MM(VD / 2))
    bl = blockers(NET, {F, pcbnew.In1_Cu, IN2, B}, c)
    if bl:
        print(f'via {vxy} blockers:', bl[:4])
        continue
    print(f'via {vxy}: CLEAN')
    chosen = vxy
    break
if chosen is None:
    print('ABORT: no via candidate clean')
    sys.exit(1)

# In2 east run: from the via to the main group's In2 segment.
RUNS = [
    [(chosen, (58.30, -15.00)), ((58.30, -15.00), (58.30, -17.38))],
    [(chosen, (57.90, -15.00)), ((57.90, -15.00), (57.90, -17.38))],
    [(chosen, (56.90, -15.00)), ((56.90, -15.00), (58.30, -17.38))],
]
run = None
for cand in RUNS:
    ok = True
    for a, b in cand:
        bl = blockers(NET, {IN2}, seg_shape(a, b, W))
        if bl:
            print('In2 run', a, '->', b, 'blockers:', bl[:4])
            ok = False
            break
    if ok:
        run = cand
        break
if run is None:
    print('ABORT: no In2 run clean')
    sys.exit(1)

add_track(STUB_END, chosen, F)
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(chosen[0]), MM(chosen[1])))
v.SetDrill(MM(0.30))
v.SetWidth(MM(VD))
v.SetViaType(pcbnew.VIATYPE_THROUGH)
v.SetLayerPair(F, B)
v.SetNet(netobj)
board.Add(v)
for a, b in run:
    add_track(a, b, IN2)

g1 = ngroups(board)
print('groups after:', g1)
assert g1 == 1, 'join failed'
repair6.save_checkpoint(board, OUT)
print('saved', OUT)
