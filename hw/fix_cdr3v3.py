#!/usr/bin/env python3
"""+3V3D_CDR haul: U4.12 stub -> U4.18 group tail, In2 bridge.

heal refuses the U4.12 group (4 s fail). The F row y=-15.45 east
is crossed by three vertical F escapes (CF2 x=55.75, CF1 x=56.25,
CDR_LOL x=56.75), so the haul bridges them on In2: via beside the
existing stub end (54.75,-15.45) -- the via cannot sit ON the stub
end: U4.13's GND pad corner is 0.407 from it (0.107 clear < 0.25);
sites ~ (54.70,-15.20) clear it at 0.294. In2 east run (the strip
has no vias and no In2 copper in the box census), via up at
~(58.55,-15.30), F run south into the U4.18 tail end (58.62,-17.38).
Variant family searched; shapes tested against the surgery item
model (zones excluded, audit verifies after refill).

Run: xvfb-run -a python3 hw/fix_cdr3v3.py IN OUT
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MMf = pcbnew.FromMM
F, In2 = pcbnew.F_Cu, pcbnew.In2_Cu
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}
NET = "+3V3D_CDR"
SRC, OUT = sys.argv[1], sys.argv[2]
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


items = build_items(board)
STUB_END = (54.75, -15.45)
JOIN = (58.62, -17.38)
chosen = None
for v1 in ((54.70, -15.20), (54.65, -15.15), (54.75, -15.15),
           (54.60, -15.20), (54.80, -15.25)):
    bad = blocked(items, NET, via_shape(*v1), ALL)
    if bad:
        print(f"  via1 {v1}: {bad}")
        continue
    bad = blocked(items, NET, seg_shape(*STUB_END, *v1, 0.25), {F})
    if bad:
        print(f"  neck to {v1}: {bad}")
        continue
    for v2 in ((58.55, -15.30), (58.60, -15.45), (58.50, -15.20),
               (58.45, -15.35)):
        shapes = [
            (seg_shape(*v1, *v2, 0.25), {In2}),
            (via_shape(*v2), ALL),
            (seg_shape(*v2, *JOIN, 0.25), {F}),
        ]
        bad = None
        for shape, layers in shapes:
            bad = blocked(items, NET, shape, layers)
            if bad:
                break
        if not bad:
            chosen = (v1, v2)
            break
    if chosen:
        break
if not chosen:
    print("NO CLEAN HAUL FOUND")
    sys.exit(1)
v1, v2 = chosen
print(f"haul: stub {STUB_END} -> via {v1} -> In2 -> via {v2} -> join {JOIN}")


def add_track(x1, y1, x2, y2, w, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MMf(x1), MMf(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MMf(x2), MMf(y2)))
    t.SetWidth(MMf(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(NET))
    board.Add(t)


def add_via(x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MMf(x), MMf(y)))
    v.SetWidth(MMf(0.6))
    v.SetDrill(MMf(0.3))
    v.SetNet(board.FindNet(NET))
    board.Add(v)


add_track(*STUB_END, *v1, 0.25, F)
add_via(*v1)
add_track(*v1, *v2, 0.25, In2)
add_via(*v2)
add_track(*v2, *JOIN, 0.25, F)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f"saved {OUT}")
