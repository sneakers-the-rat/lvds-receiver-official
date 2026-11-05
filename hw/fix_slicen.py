#!/usr/bin/env python3
"""SLICEN U4.7 escape: pure-F northern jog over SLICEP's via.

Diagnosis (this run's probe records): U4.7's west lane is fenced by
SLICEP's escape via at (51.5,-17.5) -- via disc r0.3 + track
halfwidth 0.1 + need 0.2 = 0.6 mm exclusion against a 0.25 mm row
offset. hand_stub (16 dirs x 10 lengths x 3 widths) and hand_via
both refused U4.7.

Mechanism 2 (pair re-lay, grid-searched in this file's first form):
DEAD on evidence -- SLICEP's via can only sit on its original row:
the +3V3D In2 trunk (top edge y=-18.07) fences via centres to
y >= -17.52 at need 0.25, CDR_NIN's diagonal fences the F neck west
of x~51.0, and U4.7's own pad fences the east. A relayed via on the
-17.5 row blocks SLICEN's lane identically to the original.

Mechanism 3 (this script): SLICEN stays on F and jogs NORTH over
the via: west along its row to x~52.05 (the via disc's 0.6 mm
exclusion ends at x=52.045 on this row), a steep rise to y~-16.82
passing 0.6+ from the via centre, then west into its own group's
track end at (51.38,-16.88). SLICEP is not touched. A small variant
family is searched; every shape is tested against the surgery item
model (pads/tracks/vias, zone fills excluded -- the F GND pour
re-carves at refill and the post-pass audit verifies; same model
that placed SLICEP's own escape).

First form of mechanism 3 was refused on a GND stitch via at
(52.125,-16.625) sitting in the rise corridor (its 0.6 mm exclusion
+ SLICEP via's 0.6 overlap: no line threads between them). A pour
stitch via is movable by definition, so this script first relocates
that one via NE of U4's north row (grid-searched, foreign-clean),
then runs the jog search. The post-pass audit verifies GND groups
did not grow.

Run: xvfb-run -a python3 hw/fix_slicen.py IN OUT
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
SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)


def refill(b):
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())


def build_items(b):
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


# ---------- 0. relocate the GND stitch via out of the corridor ----
items = build_items(board)
moved = None
for t in list(board.GetTracks()):
    if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "GND":
        p = t.GetPosition()
        if (round(MMt(p.x), 3), round(MMt(p.y), 3)) == (52.125, -16.625):
            for cand in ((52.45, -15.85), (52.90, -16.10), (53.40, -15.70),
                         (52.30, -15.50), (53.90, -16.10), (52.60, -15.40)):
                bad = blocked(items, "GND", via_shape(*cand), ALL)
                if not bad:
                    board.Remove(t)
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pcbnew.VECTOR2I(MMf(cand[0]), MMf(cand[1])))
                    v.SetWidth(MMf(0.6))
                    v.SetDrill(MMf(0.3))
                    v.SetNet(board.FindNet("GND"))
                    board.Add(v)
                    moved = cand
                    print(f"GND stitch via (52.125,-16.625) -> {cand}")
                    break
            break
assert moved, "no clean relocation site for the GND stitch via"
items = build_items(board)
PAD_PT = (52.20, -17.25)        # on U4.7 pad
JOINS = [(51.38, -16.88), (51.25, -16.75)]

chosen = None
for turn_x in (52.08, 52.05, 52.11, 52.02):
    for vx, vy in ((51.72, -16.82), (51.68, -16.80), (51.75, -16.84),
                   (51.66, -16.78), (51.78, -16.86), (51.62, -16.80)):
        for join in JOINS:
            pts = [PAD_PT, (turn_x, -17.25), (vx, vy), join]
            bad = None
            for i in range(len(pts) - 1):
                bad = blocked(items, "SLICEN",
                              seg_shape(*pts[i], *pts[i + 1], 0.2), {F})
                if bad:
                    break
            if not bad:
                chosen = pts
                break
        if chosen:
            break
    if chosen:
        break

if not chosen:
    print("NO CLEAN JOG FOUND")
    sys.exit(1)
print(f"jog: {chosen}")


def add_track(net, x1, y1, x2, y2, w, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MMf(x1), MMf(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MMf(x2), MMf(y2)))
    t.SetWidth(MMf(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    print(f"  +trk {net} L{layer} ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) w={w}")


for i in range(len(chosen) - 1):
    add_track("SLICEN", *chosen[i], *chosen[i + 1], 0.2, F)
refill(board)
board.Save(OUT)
print(f"saved {OUT}")
