#!/usr/bin/env python3
"""Placement relief by audit-driven nudges (placement-only boards).

For every different-footprint pad pair whose effective shapes are
closer than the project clearance (the identical rules to
hw/check_pcb.py: HV 1.0 surface / POWER 0.25 / default 0.2), move the
more movable footprint directly away from the other pad by
deficit + margin, iterating until no inter-part pad violations
remain or the round cap is hit. Same-footprint (INTRINSIC) pairs are
footprint geometry and are never touched. Zone items are ignored
here (zones refill after routing). Fixed parts (edge connectors,
the APD/TIA core) are never moved; if both sides are fixed the pair
is reported, not forced.

Run: xvfb-run -a python3 hw/relief_nudge.py IN.kicad_pcb OUT.kicad_pcb
Prints every move (ref, from -> to, why) and the before/after counts.
"""
import sys, math
import wx
_app = wx.App(False)
import pcbnew

MM = pcbnew.FromMM
HV_NETS = {"APD_K", "HV_RAW", "HV_SEC"}
POWER_NETS = {"+5V", "+3V3D", "+3V3D_CDR", "+3V3A", "+VA", "-VA",
              "NEG_RAW", "VBUS_RAW", "PHY_1V8", "PHY_1V8A"}
FIXED = {"J1", "RJ1", "RJ2", "D1", "U1"}   # edge connectors + APD/TIA core
LAYERS = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
MARGIN = 0.06      # mm beyond the bare deficit
EDGE_KEEP = 0.35   # mm, pads must stay this far inside the outline


def clearance_for(net):
    if net in HV_NETS: return 1.0
    if net in POWER_NETS: return 0.25
    return 0.2


def need_for(na, nb, shared):
    internal_only = shared and not (shared & SURFACE)
    def c(n):
        if internal_only and n in HV_NETS: return 0.3
        return clearance_for(n)
    return max(c(na), c(nb))


def pad_items(board):
    items = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net: continue
            layers = {l for l in LAYERS if pad.IsOnLayer(l)}
            items.append((fp, pad, net, layers, pad.GetEffectiveShape(),
                          pad.GetBoundingBox(), pad.GetPosition()))
    return items


def gap_mm(a_shape, b_shape, hi):
    """Actual gap in mm by bisection on SHAPE.Collide (Collide(c) is
    true iff the shapes are closer than c). Caller guarantees
    Collide(hi) is true. Collide(0) true means touching/overlapping."""
    if a_shape.Collide(b_shape, 0):
        return 0.0
    lo = 0.0            # Collide(lo) false: distance >= lo
    for _ in range(24):
        mid = (lo + hi) / 2
        if a_shape.Collide(b_shape, pcbnew.FromMM(mid)):
            hi = mid
        else:
            lo = mid
    return hi


def violations(board):
    items = pad_items(board)
    out = []
    for i in range(len(items)):
        fa, pa, na, la, sa, ba, ca = items[i]
        for j in range(i + 1, len(items)):
            fb, pb, nb, lb, sb, bb, cb = items[j]
            if na == nb or fa.GetReference() == fb.GetReference(): continue
            shared = la & lb
            if not shared: continue
            need = need_for(na, nb, shared)
            g = None
            if sa.Collide(sb, pcbnew.FromMM(need - 0.001)):
                g = gap_mm(sa, sb, need)
                if g < need - 0.001:
                    out.append((fa, pa, na, fb, pb, nb, need, g, ca, cb))
    return out


def inside(board, fp, dx, dy):
    """True if moving fp by (dx,dy) keeps all its pads EDGE_KEEP
    inside the board bounding box (outline is the 100x80 rect)."""
    for pad in fp.Pads():
        p = pad.GetPosition()
        x, y = pcbnew.ToMM(p.x) + dx, pcbnew.ToMM(p.y) + dy
        bb = pad.GetBoundingBox()
        r = max(pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())) / 2
        if x - r < EDGE_KEEP or x + r > 100 - EDGE_KEEP: return False
        if y - r < EDGE_KEEP or y + r > 80 - EDGE_KEEP: return False
    return True


def movable(fp):
    return fp.GetReference() not in FIXED


def main():
    src, dst = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard(src)
    # J2 defect: header at (97,45) rot 90 puts pads 5/6 at x=102.08,
    # 2.08 mm past the right edge. Shift the whole connector -4 mm.
    for fp in board.GetFootprints():
        if fp.GetReference() == "J2":
            p = fp.GetPosition()
            fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(93.0), p.y))
            print(f"MOVE J2 -> (93.00, {pcbnew.ToMM(p.y):.2f})  [pads 5/6 were outside outline]")
    v0 = violations(board)
    print(f"inter-part pad violations before: {len(v0)}")
    moves = []
    for rnd in range(12):
        v = violations(board)
        if not v:
            break
        progressed = False
        for fa, pa, na, fb, pb, nb, need, g, ca, cb in v:
            deficit = need - g + MARGIN
            ax, ay = pcbnew.ToMM(ca.x), pcbnew.ToMM(ca.y)
            bx, by = pcbnew.ToMM(cb.x), pcbnew.ToMM(cb.y)
            dx, dy = bx - ax, by - ay
            norm = math.hypot(dx, dy)
            if norm < 1e-6: dx, dy, norm = 1.0, 0.0, 1.0
            ux, uy = dx / norm, dy / norm
            # move the movable one with fewer pads; B preferred
            cand = []
            if movable(fb): cand.append((len(fb.Pads()), fb, +1))
            if movable(fa): cand.append((len(fa.Pads()), fa, -1))
            cand.sort(key=lambda t: t[0])
            done = False
            for _, fp, sgn in cand:
                mx, my = ux * deficit * sgn, uy * deficit * sgn
                if inside(board, fp, mx, my):
                    p = fp.GetPosition()
                    fp.SetPosition(pcbnew.VECTOR2I(
                        p.x + pcbnew.FromMM(mx), p.y + pcbnew.FromMM(my)))
                    moves.append((fp.GetReference(),
                                  (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)),
                                  (pcbnew.ToMM(p.x) + mx, pcbnew.ToMM(p.y) + my),
                                  f"{na}({pa.GetNumber()}) vs {nb}({pb.GetNumber()}) gap {g:.3f} < {need}"))
                    done = progressed = True
                    break
            if not done:
                print(f"  UNMOVABLE pair: {fa.GetReference()}.{pa.GetNumber()} [{na}] vs "
                      f"{fb.GetReference()}.{pb.GetNumber()} [{nb}] gap {g:.3f} need {need}")
        print(f"round {rnd}: {len(v)} violations at round start")
        if not progressed:
            break
    vf = violations(board)
    print(f"inter-part pad violations after: {len(vf)}")
    for ref, a, b, why in moves:
        print(f"MOVE {ref}: ({a[0]:.2f},{a[1]:.2f}) -> ({b[0]:.2f},{b[1]:.2f})  [{why}]")
    for fa, pa, na, fb, pb, nb, need, g, ca, cb in vf:
        print(f"REMAIN {fa.GetReference()}.{pa.GetNumber()} [{na}] vs "
              f"{fb.GetReference()}.{pb.GetNumber()} [{nb}] gap {g:.3f} need {need}")
    board.Save(dst)
    print("saved", dst)

if __name__ == "__main__":
    main()
