#!/usr/bin/env python3
"""Connect CDR_LOL's lone pad U6.36 (queue item 6b).

U6.36's west stub ends at (70.50,2.75); the main group's In2
trunk runs at x=56.62 through y=2.75. Mechanism: extend the stub
west, dive, and run In2 west onto the trunk. Heal refused the
group in 1s (pad-cell seal in its grid). Candidates exact-tested
in order; groups must go 2 -> 1 or the board is not saved.

Run: xvfb-run -a python3 hw/fix_lol.py IN OUT
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
NET = 'CDR_LOL'
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

STUB_END = (70.50, 2.75)
# ULPI_NXT's B diagonal (70.05,0.12)->(70.30,5.30) fences every dive
# on the y=2.75 latitude. Route: F west to x=70.15, south to y=1.60,
# east under U6.37's pad, dive at (70.85,1.60), In2 west to the trunk.
FPATH = [((70.50, 2.75), (70.15, 2.75)), ((70.15, 2.75), (70.15, 1.60)),
         ((70.15, 1.60), (70.85, 1.60))]
VIA = (70.85, 1.60)
for a, b in FPATH:
    bl = blockers(NET, {F}, seg_shape(a, b, W))
    print('F path', a, '->', b, 'blockers:', bl[:4] if bl else 'none')
    if bl:
        print('ABORT: F path blocked')
        sys.exit(1)
c = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(VIA[0]), MM(VIA[1])), MM(VD / 2))
bl = blockers(NET, {F, pcbnew.In1_Cu, IN2, B}, c)
print(f'via {VIA} blockers:', bl[:4] if bl else 'none')
if bl:
    print('ABORT: via blocked')
    sys.exit(1)
chosen = VIA

RUNS = [
    [(chosen, (56.62, 1.60))],
    [(chosen, (70.85, 1.10)), ((70.85, 1.10), (56.62, 1.10))],
    [(chosen, (70.85, 2.10)), ((70.85, 2.10), (56.62, 2.10))],
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

for a, b in FPATH:
    add_track(a, b, F)
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
