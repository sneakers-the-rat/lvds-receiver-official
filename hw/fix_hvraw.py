#!/usr/bin/env python3
"""HV_RAW repair: rip heal's B.Cu surface diagonal (32 zone-clearance
violations vs the GND pour, exp81 audit) and re-bridge the D9.1 haul
on In2, where the HV class is the buried 0.3 mm rule and no GND zone
exists. Candidate via sites and segments are tested against the
audit's OWN item model (check_pcb: pads/tracks/vias + zone FILLS,
need_for classes) -- zones included, unlike the surgery testers,
because this failure species is precisely zone proximity.

Path: D9.1 (3.85,-25.00) -F neck-> via V -In2-> via W (34.12,-11.88,
proven clean in the exp81 audit) -F neck-> (34.75,-12) -> D5.1 web.

Usage: xvfb-run -a python3 hw/fix_hvraw.py rip IN OUT
       xvfb-run -a python3 hw/fix_hvraw.py place IN OUT
(two processes: a second in-process LoadBoard after Remove/Fill
returns a broken swig proxy on this KiCad build.)
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
F, In1, In2, B = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
ALL = {F, In1, In2, B}
NET = "HV_RAW"
MODE, SRC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
board = pcbnew.LoadBoard(SRC)


def refill():
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())


def build_items_full(b):
    """check_pcb.main's item construction, zones included."""
    items = []
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            layers = {l for l in (F, In1, In2, B) if pad.IsOnLayer(l)}
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
    for z in b.Zones():
        net = z.GetNetname()
        layer = z.GetLayer()
        poly = z.GetFilledPolysList(layer)
        if poly.OutlineCount() == 0:
            continue
        items.append(("zone", net, {layer}, poly, f"zone L{layer}"))
    return items


def blocked(items, net, shape, layers):
    for kind, n2, l2, s2, desc in items:
        if n2 == net:
            continue
        shared = layers & l2
        if not shared:
            continue
        if kind == "zone" and not (shared & check_pcb.SURFACE):
            # Buried-layer zone interaction is governed by the zone's
            # own carve at refill (In1 GND carve 0.35 >= 0.3 buried HV
            # need; exp81 audit shows W's via clean). The refill +
            # post-pass audit verifies; only surface shares are
            # placement-tested here.
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


# ---------- 1. rip heal's HV_RAW additions ----------
def key(t):
    s, e = t.GetStart(), t.GetEnd()
    return (round(MMt(s.x), 2), round(MMt(s.y), 2),
            round(MMt(e.x), 2), round(MMt(e.y), 2))


RIP_F = {(3.85, -25.00, 4.10, -25.00), (4.10, -25.00, 4.12, -24.88),
         (4.12, -24.88, 5.38, -24.88), (34.12, -11.88, 34.75, -12.00),
         (34.75, -12.00, 35.50, -12.00)}
RIP_VIA = {(5.38, -24.88), (34.12, -11.88)}
removed = 0
for t in list(board.GetTracks()):
    if t.GetNetname() != NET:
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        if (round(MMt(p.x), 2), round(MMt(p.y), 2)) in RIP_VIA:
            board.Remove(t)
            removed += 1
    elif t.GetLayer() == B or (t.GetLayer() == F and key(t) in RIP_F):
        board.Remove(t)
        removed += 1
print(f"ripped {removed} heal-added HV_RAW items")
refill()
board.Save(OUT)
print(f"saved {OUT} (rip phase)")
if MODE == "rip":
    sys.exit(0)

# D9 pour notch (hw/notch.py species): rule areas, copper-pour
# keepout only, over the D9.1 pad + neck + via pocket expanded by
# 1.35 mm, so the F/B GND pours hold >=1.0 mm from the HV copper.
# (Also cures the pre-existing exp79 line 'HV_RAW (D9.1) vs GND
# zone L0'.)
NOTCH = (1.25, -27.50, 7.03, -22.50)
for layer in (F, B):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowCopperPour(True)
    z.SetLayer(layer)
    o = z.Outline()
    o.NewOutline()
    x0, y0, x1, y1 = NOTCH
    for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(pcbnew.VECTOR2I(MMf(x), MMf(y)))
    board.Add(z)
refill()
print(f"notch {NOTCH} added on F+B, refilled")
items = build_items_full(board)

# ---------- 2. candidate search ----------
W = (34.12, -11.88)
bad = blocked(items, NET, via_shape(*W), ALL)
print(f"web-end via W {W}: {'CLEAR' if not bad else bad}")
assert not bad, "W via no longer clean -- stop"
bad = blocked(items, NET, seg_shape(W[0], W[1], 34.75, -12.00, 0.2), {F})
assert not bad, f"W neck 1: {bad}"
bad = blocked(items, NET, seg_shape(34.75, -12.00, 35.50, -12.00, 0.2), {F})
assert not bad, f"W neck 2: {bad}"

VIA_CANDS = [(5.38, -24.88), (6.40, -25.90), (5.20, -26.60),
             (7.20, -24.90), (6.60, -24.20), (8.20, -25.90),
             (9.40, -24.88), (7.80, -26.80), (11.00, -24.88),
             (5.00, -23.40), (12.60, -24.88), (4.60, -27.40),
             (9.00, -27.20), (13.50, -26.50)]
PAD = (3.85, -25.00)


def in2_paths(v):
    # Occupancy-derived (results: In2 southern-band dump, exp82):
    # free water along y=-24.88; +5V trunk at x=24.9 (y -26.6..-19.9)
    # fences the east; corridor at x~22.2 runs north between the
    # HV_SHDN web (ends x=20.5) and the +5V staircase/via field.
    yield [v, (22.2, -24.88), (22.2, -13.5), (24.5, -10.8),
           (28.0, -11.88), W]
    yield [v, (22.2, -24.88), (22.2, -14.5), (24.8, -11.2),
           (29.0, -11.5), W]
    yield [v, (22.2, -24.88), (22.2, -13.5), W]
    yield [v, (22.2, -24.88), (22.2, -14.5), (27.0, -13.2), W]
    yield [v, (23.8, -24.88), (23.8, -19.8), (21.5, -16.0), W]
    yield [v, W]
    for wp in [(20.0, -22.0), (24.0, -18.0), (18.0, -24.88),
               (26.0, -22.0), (14.0, -17.0), (22.0, -24.88)]:
        yield [v, wp, W]
    yield [v, (18.0, -24.88), (28.0, -16.0), W]
    yield [v, (24.0, -24.88), (30.0, -15.0), W]


chosen = None
for v in VIA_CANDS:
    bad = blocked(items, NET, via_shape(*v), ALL)
    if bad:
        print(f"  via {v}: {bad}")
        continue
    bad = blocked(items, NET, seg_shape(PAD[0], PAD[1], v[0], v[1], 0.4), {F})
    if bad:
        print(f"  via {v}: neck {bad}")
        continue
    for path in in2_paths(v):
        badseg = None
        for i in range(len(path) - 1):
            b2 = blocked(items, NET,
                         seg_shape(path[i][0], path[i][1],
                                   path[i + 1][0], path[i + 1][1], 0.4),
                         {In2})
            if b2:
                badseg = f"seg{i} {b2}"
                break
        if not badseg:
            chosen = (v, path)
            print(f"  via {v}: CLEAR, In2 path {path}")
            break
        else:
            print(f"  via {v}: path {path} blocked: {badseg}")
    if chosen:
        break

assert chosen, "no (via, In2 path) candidate cleared -- board NOT saved"
V, path = chosen

# ---------- 3. place ----------
def add_track(net, x1, y1, x2, y2, w, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MMf(x1), MMf(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MMf(x2), MMf(y2)))
    t.SetWidth(MMf(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    print(f"  +trk L{layer} ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) w={w}")


def add_via(net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MMf(x), MMf(y)))
    v.SetWidth(MMf(0.6))
    v.SetDrill(MMf(0.3))
    v.SetNet(board.FindNet(net))
    board.Add(v)
    print(f"  +via ({x:.2f},{y:.2f})")


add_track(NET, PAD[0], PAD[1], V[0], V[1], 0.4, F)
add_via(NET, *V)
for i in range(len(path) - 1):
    add_track(NET, path[i][0], path[i][1], path[i + 1][0], path[i + 1][1],
              0.4, In2)
add_via(NET, *W)
add_track(NET, W[0], W[1], 34.75, -12.00, 0.2, F)
add_track(NET, 34.75, -12.00, 35.50, -12.00, 0.2, F)
refill()
board.Save(OUT)
print(f"saved {OUT}")
