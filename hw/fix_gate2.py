#!/usr/bin/env python3
"""Gate re-weave phase 2: clocks first, +3V3D_CDR last.

heal connected +3V3D_CDR on the ripped gate (pass-112 field), but
its chosen route -- via (54.38,-14.38), F diagonal, stub extension,
B staircase west -- seals BOTH clock pad stubs in turn: REFCLK's
via field is tiled by the THRADJ-vertical / THRADJ-jog / +3V3D-via
discs, REFCLKN's NE quadrant by the +3V3D via + stub extension +
B staircase start. Verified by exhaustive via-site analysis in
this session's probes.

Order of operations on exp92:
  rip: +3V3D_CDR's heal route in the gate (7 items: F stub
       extension, F diagonal, via (54.38,-14.38), 4 B staircase
       segments). +3V3D_CDR returns to 3 groups; heal re-runs LAST.
  lay REFCLKN (F): stub end (54.25,-15.12) -> north (54.25,-14.55)
       -> flat east into its tail start (55.5,-14.5).
  lay REFCLK (F): stub end (53.75,-15.12) -> north (53.75,-12.80)
       -> east (56.90,-12.80) -> via -> In2 south into its own In2
       run (56.90,-13.88). (The direct F east run at y=-13.55 dies
       on REFCLKN's tail diagonal; the y=-12.8 line crosses only
       inner layers.)
  then: xvfb-run -a python3 hw/heal_nets.py exp93 exp94 +3V3D_CDR

All lay shapes tested against the surgery item model (zones
excluded, audit verifies after refill).

Run: xvfb-run -a python3 hw/fix_gate2.py rip|lay IN OUT
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
F, In2 = pcbnew.F_Cu, pcbnew.In2_Cu
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
    for a, c in (((54.75, -16.06), (54.75, -14.56)),
                 ((54.75, -14.56), (54.38, -14.38)),
                 ((54.38, -14.38), (54.12, -14.38)),
                 ((54.12, -14.38), (53.88, -14.62)),
                 ((53.88, -14.62), (53.62, -14.88)),
                 ((53.62, -14.88), (51.62, -14.88))):
        RIP.add((*a, *c))
        RIP.add((*c, *a))
    ripped = 0
    for t in list(board.GetTracks()):
        if t.GetNetname() != "+3V3D_CDR":
            continue
        if key(t) in RIP:
            board.Remove(t)
            ripped += 1
        elif (isinstance(t, pcbnew.PCB_VIA)
              and abs(MMt(t.GetPosition().x) - 54.38) < 0.01
              and abs(MMt(t.GetPosition().y) + 14.38) < 0.01):
            board.Remove(t)
            ripped += 1
    print(f"ripped {ripped} +3V3D_CDR gate items (expect 7)")
    assert ripped == 7, "rip set mismatch -- stop"
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


items = build_items(board)

# REFCLKN: (54.25,-15.12) -> (54.25,-14.55) -> (55.5,-14.5)
N_NET = "REFCLKN"
for shape, layers in [
        (seg_shape(54.25, -15.12, 54.25, -14.55, 0.2), {F}),
        (seg_shape(54.25, -14.55, 55.50, -14.50, 0.2), {F})]:
    bad = blocked(items, N_NET, shape, layers)
    if bad:
        print(f"REFCLKN lay blocked: {bad}")
        sys.exit(1)
print("REFCLKN shapes clean")

# REFCLK: (53.75,-15.12) -> north -> swerve east over THRADJ's jog
#         end (53.38,-13.88) -> (54.05,-12.80) -> east -> via
#         (56.90,-12.80) -> In2 (56.90,-13.88)
K_NET = "REFCLK"
K_PATH = [(53.75, -15.12), (53.75, -14.60), (54.20, -13.70),
          (54.20, -12.80), (55.40, -12.30)]
for a, c in zip(K_PATH, K_PATH[1:]):
    bad = blocked(items, K_NET, seg_shape(*a, *c, 0.2), {F})
    if bad:
        print(f"REFCLK lay blocked {a}->{c}: {bad}")
        sys.exit(1)
for shape, layers in [
        (via_shape(55.40, -12.30), ALL),
        (seg_shape(55.40, -12.30, 57.35, -12.35, 0.2), {pcbnew.B_Cu}),
        (via_shape(57.35, -12.35), ALL),
        (seg_shape(57.35, -12.35, 57.35, -13.65, 0.2), {In2})]:
    bad = blocked(items, K_NET, shape, layers)
    if bad:
        print(f"REFCLK lay blocked: {bad}")
        sys.exit(1)
print("REFCLK shapes clean")


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


add_track(N_NET, 54.25, -15.12, 54.25, -14.55, 0.2, F)
add_track(N_NET, 54.25, -14.55, 55.50, -14.50, 0.2, F)
for a, c in zip(K_PATH, K_PATH[1:]):
    add_track(K_NET, *a, *c, 0.2, F)
add_via(K_NET, 55.40, -12.30)
add_track(K_NET, 55.40, -12.30, 57.35, -12.35, 0.2, pcbnew.B_Cu)
add_via(K_NET, 57.35, -12.35)
add_track(K_NET, 57.35, -12.35, 57.35, -13.65, 0.2, In2)
refill(board)
board.Save(OUT)
print(f"saved {OUT}")
