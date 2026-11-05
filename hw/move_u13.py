#!/usr/bin/env python3
"""U13 move for SET_P (decided: west move; executed: SW relocation).

U13.7 (SET_P) is sealed at (49.55,62.5). The decided (-4,0) west
move is REFUTED on the current field (this script's exact check):
the destination footprint lands in the routed NEG_RAW staircase
web -- EP vs 18 NEG_RAW tracks, ILIM_P/+5V pins vs more, all at
need 0.25. A full-ring placement search (rect model, this file's
search mode) over dx [-8,+2] x dy [-7,+7] found exactly one clean
cluster: dx -6.75..-8, dy -6.75..-7 (plus the current position).
Executed move: (-6.75,-7.00) -> U13 at (41.25,55.00), pin 7 at
(42.80,55.50), 0.47 mm from the SET_P web (its F staircase reaches
(43.72,55.32)/(44.66,54.86)). The move breaks U13's other connected
nets at its pads (+5V, +VA, ILIM_P); they are re-healed in the
follow-up heal_nets run. GND is pour-joined, audit-verified.

Pre-check: every moved pad shape tested against all foreign items
(surgery model, zones excluded); abort if any blocks.

Run: xvfb-run -a python3 hw/move_u13.py rip IN OUT
     xvfb-run -a python3 hw/move_u13.py move IN OUT
(two processes: build_items after Remove hits the broken swig
proxy on this KiCad build -- fix_hvraw rule.)
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
MODE, SRC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DX = float(sys.argv[4]) if len(sys.argv) > 4 else -4.0
DY = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
board = pcbnew.LoadBoard(SRC)


def build_items(b, skip_ref=None):
    items = []
    for fp in b.GetFootprints():
        if fp.GetReference() == skip_ref:
            continue
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


# Rip the one SET_P web vertex inside the destination footprint:
# via (43.875,61.375) + its In2 and B segments into (43.88,61.38).
# The queue item is "move + re-heal SET_P"; heal re-bridges the web.
def key(t):
    s, e = t.GetStart(), t.GetEnd()
    return (round(MMt(s.x), 2), round(MMt(s.y), 2),
            round(MMt(e.x), 2), round(MMt(e.y), 2))


if MODE == "rip":
    ripped = 0
    for t in list(board.GetTracks()):
        if t.GetNetname() != "SET_P":
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            if (round(MMt(p.x), 3), round(MMt(p.y), 3)) == (43.875, 61.375):
                board.Remove(t)
                ripped += 1
        elif key(t) in {(43.62, 61.62, 43.88, 61.38),
                        (43.88, 61.38, 43.62, 61.62),
                        (43.88, 61.38, 44.12, 61.12),
                        (44.12, 61.12, 43.88, 61.38)}:
            board.Remove(t)
            ripped += 1
    print(f"ripped {ripped} SET_P web items (expect 3)")
    assert ripped == 3, "rip set mismatch -- stop"
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(OUT)
    print(f"saved {OUT} (rip phase)")
    sys.exit(0)

items = build_items(board, skip_ref="U13")
fp = board.FindFootprintByReference("U13")

if MODE == "search":
    import math

    def pad_rect(pad, dx, dy):
        # NOTE: pad.GetEffectiveShape() is a LIVE VIEW on this build --
        # Move() on it mutates the pad's cached shape, so repeated
        # translations accumulate (first search run was garbage).
        # U13 is rot=0 with rectangular pads: build a fresh SHAPE_RECT
        # per query. The exact single-translation check in move mode
        # remains the gate.
        p = pad.GetPosition()
        w = pad.GetSize().x
        h = pad.GetSize().y
        cx = p.x + MMf(dx)
        cy = p.y + MMf(dy)
        return pcbnew.SHAPE_RECT(pcbnew.VECTOR2I(cx - w // 2, cy - h // 2),
                                 int(w), int(h))

    def pads_clean(dx, dy):
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            shape = pad_rect(pad, dx, dy)
            layers = {l for l in (F, In1, In2, B) if pad.IsOnLayer(l)}
            for kind, n2, l2, s2, desc in items:
                if n2 == net:
                    continue
                shared = layers & l2
                if not shared:
                    continue
                need = need_for(net, n2, shared)
                if shape.Collide(s2, MMf(need - 0.001)):
                    return False
        return True

    def pin7_gap(dx, dy):
        # distance from moved pin-7 pad shape to nearest SET_P item
        pad7 = None
        for pad in fp.Pads():
            if pad.GetNumber() == "7":
                pad7 = pad
        shape = pad_rect(pad7, dx, dy)
        best = 99.0
        for kind, n2, l2, s2, desc in items:
            if n2 != "SET_P":
                continue
            lo, hi = 0.0, 10.0
            if shape.Collide(s2, MMf(hi)):
                for _ in range(24):
                    mid = (lo + hi) / 2
                    if shape.Collide(s2, MMf(mid)):
                        hi = mid
                    else:
                        lo = mid
                best = min(best, hi)
        return best

    results = []
    dx = -8.0
    while dx <= 2.05:
        dy = -7.0
        while dy <= 7.05:
            if pads_clean(dx, dy):
                results.append((pin7_gap(dx, dy),
                                abs(dx + 4.0) + abs(dy), dx, dy))
            dy += 0.25
        dx += 0.25
    results.sort()
    for gap, dev, dx, dy in results[:15]:
        print(f"  clean dx={dx:+.2f} dy={dy:+.2f} pin7gap={gap:.2f} dev={dev:.2f}")
    print(f"{len(results)} clean placements")
    sys.exit(0)
pos = fp.GetPosition()
print(f"U13 at ({MMt(pos.x):.2f},{MMt(pos.y):.2f}) -> "
      f"({MMt(pos.x) + DX:.2f},{MMt(pos.y) + DY:.2f})")

# Test each pad's shape translated by (DX,DY) against foreign items.
bad_all = []
for pad in fp.Pads():
    net = pad.GetNetname()
    if not net:
        continue
    shape = pad.GetEffectiveShape()
    shape.Move(pcbnew.VECTOR2I(MMf(DX), MMf(DY)))
    layers = {l for l in (F, In1, In2, B) if pad.IsOnLayer(l)}
    for kind, n2, l2, s2, desc in items:
        if n2 == net:
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        if shape.Collide(s2, MMf(need - 0.001)):
            bad_all.append(f"{pad.GetNumber()} ({net}) vs {n2} {desc} need{need}")
for b_ in bad_all:
    print("  BLOCKED:", b_)
assert not bad_all, "moved footprint collides -- stop"

fp.SetPosition(pcbnew.VECTOR2I(pos.x + MMf(DX), pos.y + MMf(DY)))
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f"saved {OUT}")
