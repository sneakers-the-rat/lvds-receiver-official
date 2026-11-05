#!/usr/bin/env python3
"""U13.6 (+5V) hand bridge after the U13 relocation: two-via In2 hop.

heal refused U13.6's group twice (Class B cost-model species).
Second mechanism (pure-F west bridge) refused on evidence: the
F field west of the stub is a GND/DM_PHY/ILIM_P braid (GND F
staircase at y~56.9 fences every west-leg row at need 0.25), and
the ILIM_P/EP corridor is 0.445 wide < 0.6 needed.

This mechanism (3rd form): ONE via beside the pad, then a single
B.Cu run NW into the +5V B staircase track (41.62,53.38)->
(41.88,53.12) at its midpoint (41.75,53.25) -- the same B web that
joined pins 1/2/3. The In2 hop form was refused on evidence:
DM_PHY's In2 run is a continuous 45-degree highway from
(39.88,57.88) through (45,52.4) to U7 -- it has no end to round;
every A->B segment paralleled it inside the 0.25 need. B.Cu in
this box carries only the ILIM_P (SW) and SET_P (SE) staircases.
Every shape tested against the surgery item model, zones
excluded, audit verifies.

Run: xvfb-run -a python3 hw/fix_u13_6.py IN OUT
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
F, In2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}
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
JOIN_B = (41.75, 53.25)
# Via1 cannot sit at the stub end (42.30,56.50): only 0.38 from the
# GND EP corner -- a 0.2 track fits (0.278 >= 0.25) but a via disc
# does not (0.078 < 0.25). Via1 candidates sit SE along the stub,
# overlapping U13.6's pad directly (pad rect x 42.475..43.125,
# y 55.85..56.15).
chosen = None
for VIA1 in ((42.68, 56.28), (42.72, 56.32), (42.64, 56.24), (42.76, 56.36)):
    bad = blocked(items, "+5V", via_shape(*VIA1), ALL)
    if bad:
        print(f"  via1 {VIA1}: {bad}")
        continue
    bad = blocked(items, "+5V", seg_shape(*VIA1, *JOIN_B, 0.2), {B})
    if bad:
        print(f"  via1 {VIA1} B run: {bad}")
        continue
    chosen = VIA1
    break
if not chosen:
    print("NO CLEAN HOP FOUND")
    sys.exit(1)
VIA1 = chosen
print(f"hop: via1 {VIA1} -> B run -> join {JOIN_B}")


def add_track(x1, y1, x2, y2, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MMf(x1), MMf(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MMf(x2), MMf(y2)))
    t.SetWidth(MMf(0.2))
    t.SetLayer(layer)
    t.SetNet(board.FindNet("+5V"))
    board.Add(t)


def add_via(x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MMf(x), MMf(y)))
    v.SetWidth(MMf(0.6))
    v.SetDrill(MMf(0.3))
    v.SetNet(board.FindNet("+5V"))
    board.Add(v)


add_via(*VIA1)
add_track(*VIA1, *JOIN_B, B)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f"saved {OUT}")
