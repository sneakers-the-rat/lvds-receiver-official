#!/usr/bin/env python3
"""Connect +3V3A's lone pad U7.25 (queue item 4).

Refused mechanisms, on record:
  * via on the pad / onto the In2 mesh NE: the QFN row pitch
    (0.25 mm pads, 0.5 mm pitch, PHY_1V8 at 0.25 class) forbids
    any via at the pad; the mesh's NE staircase is shadowed by
    ULPI_CK's F staircase at the 0.25 class on every site.
  * F run west along the channel: ULPI_CK's diagonal wall, the
    CDR_DATP via (76.88,10.62), and the XI / PHY_1V8A escape nubs
    (caps to y=10.93) tile the channel completely -- 4 variants
    refused by exact test (DATP via + CK tracks + PHY_1V8 pad).

Working mechanism: a via in the north-east corner at
(78.02,11.68), d=0.45. It overlaps U7.25's own pad edge (same
net), clears U7.24 (ULPI_D0) pad by 0.25 of shape distance, and
on In2 it touches the mesh segment (77.88,11.62)->(77.62,11.88).
A two-segment F stub joins pad to via. Candidates exact-tested
in order (all layers for the via, zones excluded); groups must
go 2 -> 1 or the board is not saved.

Run: xvfb-run -a python3 hw/fix_3v3a.py IN OUT
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
NET = '+3V3A'
W = 0.20
VD = 0.45

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

def via_blockers(x, y):
    c = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(x), MM(y)), MM(VD / 2))
    return blockers(NET, {F, pcbnew.In1_Cu, pcbnew.In2_Cu, B}, c)

# (via_xy, [stub segments from the pad])
CANDS = [
    ((77.98, 11.65), [((77.80, 11.75), (77.98, 11.65))]),
    ((78.02, 11.68), [((77.80, 11.80), (78.02, 11.68))]),
    ((78.05, 11.70), [((77.82, 11.78), (78.05, 11.70))]),
    ((77.95, 11.60), [((77.78, 11.70), (77.95, 11.60))]),
]

chosen = None
for via_xy, stub in CANDS:
    bl = via_blockers(*via_xy)
    if bl:
        print(f"via {via_xy}: {bl[:4]}")
        continue
    ok = True
    for a, b in stub:
        bl = blockers(NET, {F}, seg_shape(a, b, W))
        if bl:
            print(f"via {via_xy} stub {a}->{b}: {bl[:4]}")
            ok = False
            break
    if ok:
        print(f"via {via_xy}: CLEAN")
        chosen = (via_xy, stub)
        break
if chosen is None:
    print("all candidates refused; board NOT saved")
    sys.exit(1)

via_xy, stub = chosen
netobj = board.FindNet(NET)
for a, b in stub:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(W))
    t.SetLayer(F)
    t.SetNet(netobj)
    board.Add(t)
    print(f"  stub {a}->{b}")
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(via_xy[0]), MM(via_xy[1])))
v.SetWidth(MM(VD))
v.SetDrill(MM(0.25))
v.SetViaType(pcbnew.VIATYPE_THROUGH)
v.SetLayerPair(F, B)
v.SetNet(netobj)
board.Add(v)
print(f"  via {via_xy} d={VD}")

groups = repair.compute_groups(board)
print(f"{NET}: {len(groups[NET])} group(s)")
assert len(groups[NET]) == 1, "+3V3A not rejoined!"
repair6.save_checkpoint(board, OUT)
print(f"saved {OUT}")
