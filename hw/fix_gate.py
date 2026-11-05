#!/usr/bin/env python3
"""U4 north-gate re-weave: +3V3D_CDR haul through a three-way deadlock.

Five mechanisms refused U4.12's group (heal, hand_stub, hand_via,
thread_far 'anchor stub walled at start', via-grid bridge). The
gate north of U4's 0.5 mm pad row is a woven wall: THRADJ's escape
fences REFCLK's via field, REFCLK's F diagonal fences REFCLKN's
via field and its vertical extension, REFCLKN's F diagonal jog
crosses +3V3D_CDR's channel (x=54.75), CF1's B staircase fences
the via field from the east. No single net can move.

Re-weave, in order:
  rip: REFCLK's F diagonal (4 segments (53.88,-14.88)..(54.62,-14.12)),
       REFCLKN's F jog (2 segments (54.35,-15.03)..(55.5,-14.5)), and
       REFCLK's junction via at (54.62,-14.12) + its first In2 segment
       -- that via's 0.6 mm exclusion disc fences every north channel
       (0.13 from the x=54.75 slot). Both clock nets become 2-group;
       their rejoin tails stay (REFCLK's In2 step from (55.88,-13.88);
       REFCLKN's F tail from (55.5,-14.5)).
  lay: +3V3D_CDR channel in the cleared gate (3rd form; via sites
       in the gate are tiled out by the REFCLK-via / CF1-B-stair /
       REFCLKN-tail exclusions, and the w=0.25 form of the north
       run missed the slot by millimetres): the net's own width is
       0.2, and at w=0.2 the F slot between REFCLKN's vertical and
       U4.13's pad is x in [54.70,54.77] -- the stub's own column.
       F run x=54.75 w=0.2 north from the stub end (54.75,-15.45)
       to (54.75,-13.40) -> via -> In2 east at y=-13.40 (0.48 clear
       of REFCLK's In2 step) -> via at (58.62,-13.40) -> F south in
       the tail's own column into (58.62,-17.38).
  then heal_nets REFCLK REFCLKN re-joins the clock pair in the
  changed field (separate step, not this script).

All lay shapes tested against the surgery item model (zones
excluded, audit verifies after refill).

Run: xvfb-run -a python3 hw/fix_gate.py rip IN OUT
     xvfb-run -a python3 hw/fix_gate.py lay IN OUT
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
    RIP = {
        # REFCLK F diagonal
        (53.75, -15.56, 53.88, -14.88), (53.88, -14.88, 53.75, -15.56),
        (53.88, -14.88, 54.12, -14.62), (54.12, -14.62, 53.88, -14.88),
        (54.12, -14.62, 54.38, -14.38), (54.38, -14.38, 54.12, -14.62),
        (54.38, -14.38, 54.62, -14.12), (54.62, -14.12, 54.38, -14.38),
        # REFCLKN F jog
        (54.35, -15.03, 54.5, -15.0), (54.5, -15.0, 54.35, -15.03),
        (54.5, -15.0, 55.5, -14.5), (55.5, -14.5, 54.5, -15.0),
    }
    RIP_IN2 = {(54.62, -14.12, 55.62, -14.12), (55.62, -14.12, 54.62, -14.12)}
    ripped = 0
    for t in list(board.GetTracks()):
        if t.GetNetname() in ("REFCLK", "REFCLKN") and key(t) in RIP:
            board.Remove(t)
            ripped += 1
        elif t.GetNetname() == "REFCLK" and key(t) in RIP_IN2:
            board.Remove(t)
            ripped += 1
        elif (t.GetNetname() == "REFCLK" and isinstance(t, pcbnew.PCB_VIA)
              and any(abs(MMt(t.GetPosition().x) - vx) < 0.01
                      and abs(MMt(t.GetPosition().y) - vy) < 0.01
                      for vx, vy in ((54.62, -14.12), (57.375, -13.625)))):
            # (57.375,-13.625) is REFCLK's NE junction via; its 0.65
            # exclusion walls the In2 corridor at y=-13.4. REFCLK
            # re-heal gets a second, easy gap in the open strip.
            board.Remove(t)
            ripped += 1
    print(f"ripped {ripped} gate items (expect 9)")
    assert ripped == 9, "rip set mismatch -- stop"
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
NET = "+3V3D_CDR"
STUB_END = (54.75, -15.45)
JOIN = (58.62, -17.38)
chosen = None
for run_x in (54.75, 54.73, 54.77):
    for via_y in (-13.40, -13.30, -13.50):
        v1 = (run_x, via_y)
        for mid in ((55.15, -14.55), (55.20, -14.50), (55.10, -14.60)):
            for dip in ((55.70, -15.30), (55.75, -15.28), (55.65, -15.33)):
                for v2 in ((60.30, -12.60), (60.45, -12.75),
                           (60.15, -12.45), (57.28, -14.35)):
                    shapes = [
                        (seg_shape(STUB_END[0], STUB_END[1],
                                   run_x, via_y, 0.2), {F}),
                        (via_shape(*v1), ALL),
                        (seg_shape(*v1, *mid, 0.2), {In2}),
                        (seg_shape(*mid, *dip, 0.2), {In2}),
                        (seg_shape(*dip, 57.00, -13.30, 0.2), {In2}),
                        (seg_shape(57.00, -13.30, *v2, 0.2), {In2}),
                        (via_shape(*v2), ALL),
                        (seg_shape(*v2, *JOIN, 0.2), {F}),
                    ]
                    bad = None
                    for shape, layers in shapes:
                        bad = blocked(items, NET, shape, layers)
                        if bad:
                            break
                    if not bad:
                        chosen = (v1, mid, dip, v2)
                        break
                if chosen:
                    break
            if chosen:
                break
        if chosen:
            break
    if chosen:
        break
if not chosen:
    print("NO CLEAN CHANNEL FOUND")
    sys.exit(1)
v1, mid, dip, v2 = chosen
print(f"channel: {STUB_END} -> F north -> via {v1} -> In2 {mid} -> dip "
      f"{dip} -> via {v2} -> F -> {JOIN}")


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


add_track(*STUB_END, *v1, 0.2, F)
add_via(*v1)
add_track(*v1, *mid, 0.2, In2)
add_track(*mid, *dip, 0.2, In2)
add_track(*dip, 57.00, -13.30, 0.2, In2)
add_track(57.00, -13.30, *v2, 0.2, In2)
add_via(*v2)
add_track(*v2, *JOIN, 0.2, F)
refill(board)
board.Save(OUT)
print(f"saved {OUT}")
