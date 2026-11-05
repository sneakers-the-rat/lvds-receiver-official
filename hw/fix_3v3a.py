#!/usr/bin/env python3
"""Connect +3V3A's lone pad U7.25 (queue item 4).

U7.25 (77.75,11.56) is on U7's north QFN row (0.25 mm pads on
0.5 mm pitch): a via on the pad itself would sit 0.075 mm from
U7.26 (PHY_1V8, 0.25 class) -- impossible. But the net's own In2
distribution mesh passes directly below the pad (segments around
(78.12,11.38)->(77.88,11.62)). A short F stub north-east from the
pad to a via that lands on the mesh closes the net.

Candidates are exact-tested in order (stub on F, via on all
layers, zones excluded); the group count must go 2 -> 1 or the
board is not saved.

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
SAFETY = 0.02
NET = '+3V3A'
W = 0.20

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

def via_blockers(net, x, y, d=0.6):
    c = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(x), MM(y)), MM(d / 2))
    return blockers(net, {F, pcbnew.In1_Cu, pcbnew.In2_Cu, B}, c)

# (via_xy, [stub segments]) -- stub starts must overlap the pad
# (pad spans x[77.625,77.875], y[11.12,12.00])
CANDS = [
    ((78.25, 11.30), [((77.80, 11.30), (78.25, 11.30))]),
    ((78.38, 11.12), [((77.82, 11.25), (78.38, 11.12))]),
    ((77.88, 11.62), [((77.80, 11.45), (77.88, 11.62))]),
    ((78.00, 11.45), [((77.82, 11.35), (78.00, 11.45))]),
    ((78.25, 11.30), [((77.75, 11.20), (78.05, 11.22)),
                      ((78.05, 11.22), (78.25, 11.30))]),
]

chosen = None
for via_xy, stub in CANDS:
    bl = via_blockers(NET, *via_xy)
    if bl:
        print(f"via {via_xy}: {bl[:3]}")
        continue
    ok = True
    for a, b in stub:
        bl = blockers(NET, {F}, seg_shape(a, b, W))
        if bl:
            print(f"via {via_xy} stub {a}->{b}: {bl[:3]}")
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
v.SetWidth(MM(0.6))
v.SetDrill(MM(0.3))
v.SetViaType(pcbnew.VIATYPE_THROUGH)
v.SetLayerPair(F, B)
v.SetNet(netobj)
board.Add(v)
print(f"  via {via_xy}")

groups = repair.compute_groups(board)
print(f"{NET}: {len(groups[NET])} group(s)")
assert len(groups[NET]) == 1, "+3V3A not rejoined!"
repair6.save_checkpoint(board, OUT)
print(f"saved {OUT}")
