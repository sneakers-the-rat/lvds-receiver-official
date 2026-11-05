#!/usr/bin/env python3
"""Dump HV_FBX groups + everything foreign in the (10..50, -16..6) field."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
MM = pcbnew.FromMM

board = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1
                         else 'hw/pdlvds_rx.exp106.kicad_pcb')
items = build_items(board)
# add zones like the audit does
for z in board.Zones():
    net = z.GetNetname()
    if not net:
        continue
    for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        if z.IsOnLayer(l):
            items.append(("zone", net, {l}, z.GetFilledPolysList(l),
                          f"zone L{l}"))

def centre(shape):
    bb = shape.BBox()
    return (pcbnew.ToMM(bb.Centre().x), pcbnew.ToMM(bb.Centre().y))

def bbox(shape):
    bb = shape.BBox()
    return (pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY()),
            pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight()))

NET = 'HV_FBX'
mine = [it for it in items if it[1] == NET]
print(f"== {NET} items: {len(mine)}")
# union-find on collide-0 over shared layers
n = len(mine)
parent = list(range(n))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a
for i in range(n):
    for j in range(i + 1, n):
        if mine[i][2] & mine[j][2]:
            if mine[i][3].Collide(mine[j][3], MM(0.0)):
                pi, pj = find(i), find(j)
                if pi != pj:
                    parent[pi] = pj
groups = {}
for i in range(n):
    groups.setdefault(find(i), []).append(i)
for gi, (root, idxs) in enumerate(groups.items()):
    print(f"-- group {gi}: {len(idxs)} items")
    for i in idxs:
        kind, net, layers, shape, desc = mine[i]
        ls = ','.join(str(l) for l in sorted(layers))
        print(f"   {kind} {desc} L[{ls}] centre={tuple(round(v,3) for v in centre(shape))} bbox={tuple(round(v,3) for v in bbox(shape))}")

print("== foreign pads in box x 5..55, y -18..8")
for kind, net, layers, shape, desc in items:
    if kind != 'pad' or net == NET:
        continue
    cx, cy = centre(shape)
    if 5 <= cx <= 55 and -18 <= cy <= 8:
        print(f"   {desc} {net} centre=({cx:.3f},{cy:.3f}) bbox={tuple(round(v,3) for v in bbox(shape))}")
print("== foreign tracks/vias in box x 20..45, y -12..4 (centre)")
for kind, net, layers, shape, desc in items:
    if kind not in ('track', 'via') or net == NET:
        continue
    cx, cy = centre(shape)
    if 20 <= cx <= 45 and -12 <= cy <= 4:
        ls = ','.join(str(l) for l in sorted(layers))
        print(f"   {kind} {net} L[{ls}] centre=({cx:.3f},{cy:.3f}) bbox={tuple(round(v,3) for v in bbox(shape))}")
