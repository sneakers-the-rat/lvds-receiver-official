#!/usr/bin/env python3
"""U7 west column escape: rip the palisade, lane west, heal.

The west column (+5V.4, +3V3A.6, DP_PHY.7, DM_PHY.8) faces a
two-track F palisade: CAP_CLK's vertical x=71.88 (y 11.12..17.88)
and ULPI_NXT's vertical x=72.62 (y 11.12..15.88), 0.74 mm apart --
no via fits between them (needs 0.625 each side) and no via fits
in the pad row either (0.25 pad gaps vs 0.3 via radius + needs).
The pins' own row lanes (w 0.2 in the 0.25 inter-pad gap, 0.275
clear of both neighbours) are the only F exit, and they are
walled by the palisade.

Mechanism: rip NXT's vertical + its first two diagonal steps and
CAP_CLK's vertical (4 segments; both nets' rejoins are already
owed / heal-able across the F-only lane band on inner layers),
lay the four row lanes west through both columns, end +5V and
DP_PHY on vias west of the palisade, +3V3A and DM_PHY on track
ends there (via-via spacing at 0.5 lane pitch forbids 4 vias),
XO.27 gets a north stub. heal then finishes +5V/+3V3A/DP/DM/XO
and repays NXT + CAP_CLK.

Run: xvfb-run -a python3 hw/fix_u7west.py rip IN OUT
     xvfb-run -a python3 hw/fix_u7west.py lay IN OUT
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
MMt = pcbnew.ToMM
F = pcbnew.F_Cu
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}
MODE, SRC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
board = pcbnew.LoadBoard(SRC)


def refill(b):
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())


def key(t):
    s, e = t.GetStart(), t.GetEnd()
    return (round(MMt(s.x), 2), round(MMt(s.y), 2),
            round(MMt(e.x), 2), round(MMt(e.y), 2))


if MODE == "rip":
    RIP = set()
    for a, c in (((72.62, 11.12), (72.62, 15.88)),
                 ((72.62, 15.88), (72.88, 16.12)),
                 ((72.88, 16.12), (73.12, 16.38)),
                 ((71.88, 11.12), (71.88, 17.88))):
        RIP.add((*a, *c))
        RIP.add((*c, *a))
    ripped = 0
    for t in list(board.GetTracks()):
        if t.GetNetname() in ("ULPI_NXT", "CAP_CLK") and key(t) in RIP:
            board.Remove(t)
            ripped += 1
    print(f"ripped {ripped} palisade items (expect 4)")
    assert ripped == 4, "rip set mismatch -- stop"
    refill(board)
    board.Save(OUT)
    print(f"saved {OUT} (rip phase)")
    sys.exit(0)


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
JOBS = [
    ("+5V", [(73.56, 13.75), (71.30, 13.75)], 0.25, (71.30, 13.75)),
    ("+3V3A", [(73.56, 14.75), (70.90, 14.75)], 0.25, None),
    ("DP_PHY", [(73.56, 15.25), (71.30, 15.25)], 0.2, (71.30, 15.25)),
    ("DM_PHY", [(73.56, 15.75), (70.90, 15.75)], 0.2, None),
    ("XO", [(76.75, 11.56), (76.75, 10.35)], 0.2, None),
]
for net, path, w, via in JOBS:
    bad = None
    for a, c in zip(path, path[1:]):
        bad = blocked(items, net, seg_shape(*a, *c, w), {F})
        if bad:
            break
    if not bad and via:
        bad = blocked(items, net, via_shape(*via), ALL)
    if bad:
        print(f"  {net}: BLOCKED {bad} -- skipped")
        continue
    for a, c in zip(path, path[1:]):
        add_track(net, *a, *c, w, F)
    if via:
        add_via(net, *via)
    items = build_items(board)
    print(f"  {net}: lane placed")
refill(board)
board.Save(OUT)
print(f"saved {OUT}")
