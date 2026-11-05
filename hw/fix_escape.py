#!/usr/bin/env python3
"""Wide-ring escape via for sealed residue pads.

hand_via's site rings are narrow and heal's grid walls at stub
ends inside the pad-field thicket. This searches via sites on a
0.25 mm grid over the annulus 0.8..3.2 mm around the pad (16
directions), each site audit-shape-tested on all layers, with a
shape-tested F neck from the pad edge to the via and a short In2
tail (0.9 mm, same direction) so the group gains an open-field
track anchor for the following heal. First clean site (nearest
ring first) wins per pad.

Run: xvfb-run -a python3 hw/fix_escape.py IN OUT NET:REF.PIN [...]
"""
import math
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MMf = pcbnew.FromMM
MMt = pcbnew.ToMM
F, In2 = pcbnew.F_Cu, pcbnew.In2_Cu
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}
SRC, OUT = sys.argv[1], sys.argv[2]
TARGETS = sys.argv[3:]
board = pcbnew.LoadBoard(SRC)


def build_items(b):
    items = []
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            layers = {l for l in ALL if pad.IsOnLayer(l)}
            items.append(("pad", net, layers, pad.GetEffectiveShape(),
                          f"{fp.GetReference()}.{pad.GetNumber()}"))
    for t in b.GetTracks():
        net = t.GetNetname()
        if isinstance(t, pcbnew.PCB_VIA):
            layers = set(ALL)
            kind = "via"
        else:
            layers = {t.GetLayer()}
            kind = "track"
        items.append((kind, net, layers, t.GetEffectiveShape(),
                      f"{kind}@stub"))
    return items


def blocked(items, net, shape, layers):
    for kind, n2, l2, s2, desc in items:
        if n2 == net:
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        try:
            if shape.Collide(s2, MMf(need - 0.001)):
                return f"{n2} {desc} need{need}"
        except Exception:
            return f"{n2} {desc} (collide exc)"
    return None


def seg_shape(x1, y1, x2, y2, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x1), MMf(y1)),
                                pcbnew.VECTOR2I(MMf(x2), MMf(y2)), MMf(w))


def via_shape(x, y):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x), MMf(y)),
                                pcbnew.VECTOR2I(MMf(x), MMf(y)), MMf(0.6))


def add_track(net, x1, y1, x2, y2, w, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MMf(x1), MMf(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MMf(x2), MMf(y2)))
    t.SetWidth(MMf(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)


def add_via(net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MMf(x), MMf(y)))
    v.SetWidth(MMf(0.6))
    v.SetDrill(MMf(0.3))
    v.SetNet(board.FindNet(net))
    board.Add(v)


items = build_items(board)
padpos = {}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        p = pad.GetPosition()
        padpos[f"{fp.GetReference()}.{pad.GetNumber()}"] = (
            pad.GetNetname(), MMt(p.x), MMt(p.y))

placed = 0
for spec in TARGETS:
    net, ref = spec.split(":")
    n2, px, py = padpos[ref]
    assert n2 == net, f"{spec}: pad net is {n2}"
    found = None
    for ring in (0.8, 1.05, 1.3, 1.55, 1.8, 2.05, 2.3, 2.6, 2.9, 3.2,
                 3.5, 3.75, 4.0):
        for k in range(16):
            ang = math.radians(k * 22.5)
            vx, vy = px + ring * math.cos(ang), py + ring * math.sin(ang)
            if blocked(items, net, via_shape(vx, vy), ALL):
                continue
            if blocked(items, net, seg_shape(px, py, vx, vy, 0.2), {F}):
                continue
            found = (vx, vy)
            break
        if found:
            break
    if not found:
        print(f"  {net} {ref}: NO ESCAPE VIA in 4.0mm annulus")
        continue
    vx, vy = found
    add_track(net, px, py, vx, vy, 0.2, F)
    add_via(net, vx, vy)
    items = build_items(board)
    placed += 1
    print(f"  {net} {ref}: escape via ({vx:.2f},{vy:.2f})")
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f"fix_escape done: {placed}/{len(TARGETS)} placed -> {OUT}")
