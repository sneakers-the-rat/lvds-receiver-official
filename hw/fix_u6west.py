#!/usr/bin/env python3
"""U6 west column: CAP_CLK U6.34 + CDR_LOL U6.36 escapes.

ULPI_NXT's F vertical at x=70.12 (y -0.12..5.38) fences both
pads' west lanes, and no via fits beside it (0.33 mm to the only
lane-side sites vs 0.625 needed). Mechanism (palisade precedent):
rip NXT's vertical segment (70.12,0.12)->(70.12,3.12), lay the
two F lanes west to (69.90,y) anchors, and repay NXT in the same
script with a B.Cu hop: vias on its two stub ends (70.12,0.12)
and (70.12,3.12) + B segment between them (BOOT0's B vertical at
x=70.38 starts at y=6.62, clear of the hop).

Phases: rip | lanes | repay -- separate processes (one
LoadBoard per process after edits).

Run: xvfb-run -a python3 hw/fix_u6west.py rip IN OUT
     xvfb-run -a python3 hw/fix_u6west.py lanes IN OUT
     xvfb-run -a python3 hw/fix_u6west.py repay IN OUT
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
F, B = pcbnew.F_Cu, pcbnew.B_Cu
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
    RIP = {(70.12, 3.12, 70.38, 3.38), (70.38, 3.38, 70.12, 3.12)}
    ripped = 0
    for t in list(board.GetTracks()):
        if t.GetNetname() == "ULPI_NXT" and key(t) in RIP:
            board.Remove(t)
            ripped += 1
    print(f"ripped {ripped} NXT vertical segment (expect 1)")
    assert ripped == 1, "rip set mismatch -- stop"
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
if MODE == "lanes":
    JOBS = [
        ("CAP_CLK", [(71.34, 1.75), (69.90, 1.75)], 0.2, None),
        ("CDR_LOL", [(71.34, 2.75), (69.90, 2.75)], 0.2, None),
    ]
else:
    JOBS = [
        ("ULPI_NXT", [(70.05, 0.12), (70.30, 5.30)], 0.2, "repay2"),
    ]
for net, path, w, kind in JOBS:
    if kind == "repay2":
        necks = [((70.12, 0.12), path[0]), ((70.62, 3.62), path[1])]
        bad = None
        for vx, vy in path:
            bad = blocked(items, net, via_shape(vx, vy), ALL)
            if bad:
                break
        if not bad:
            bad = blocked(items, net, seg_shape(*path[0], *path[1], w), {B})
        if not bad:
            for a, c in necks:
                bad = blocked(items, net, seg_shape(*a, *c, w), {F})
                if bad:
                    break
        if bad:
            print(f"  {net} repay: BLOCKED {bad} -- skipped")
            continue
        for vx, vy in path:
            add_via(net, vx, vy)
        add_track(net, *path[0], *path[1], w, B)
        for a, c in necks:
            add_track(net, *a, *c, w, F)
        print(f"  {net}: B hop + necks placed")
        continue
    bad = None
    for a, c in zip(path, path[1:]):
        bad = blocked(items, net, seg_shape(*a, *c, w), {F})
        if bad:
            break
    if bad:
        print(f"  {net}: BLOCKED {bad} -- skipped")
        continue
    for a, c in zip(path, path[1:]):
        add_track(net, *a, *c, w, F)
    items = build_items(board)
    print(f"  {net}: lane placed")
refill(board)
board.Save(OUT)
print(f"saved {OUT}")
