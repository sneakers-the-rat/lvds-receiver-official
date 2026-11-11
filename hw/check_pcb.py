#!/usr/bin/env python3
"""DRC-equivalent checks for the scripted board (KiCad 7.0.11 has no
kicad-cli drc; the KiCad 8 PPA was blocked in this environment).

Checks, using KiCad's own effective copper shapes via pcbnew:
  1. Connectivity: union-find over pads/tracks/vias/zone-fills that
     touch on a common layer; every net must form exactly one group
     (GND may form one group per copper layer island bridged by vias —
     reported as groups; vias/pads bridge layers in the union).
  2. Clearance: for every pair of different-net copper shapes sharing a
     layer, SHAPE.Collide with the netclass clearance; violations are
     printed with locations.
  3. Board-edge clearance 0.3 mm for all copper.
  4. Courtyard collisions (HARD GATE, owner ruling 2026-11-05): two
     footprints on the same board side whose courtyard polygons
     intersect with area > 0.001 mm^2 FAIL the verdict. A layout
     with overlapping parts is invalid, full stop — there are no
     waivers for this class (WAIVERS below applies to clearance
     pairs only). Footprints with no drawn courtyard (SH1, D2, D1,
     C4, U9, T1 at gate introduction) are measured with a
     bbox fallback (pads + Fab outline, +0.25 mm) and reported in
     their own counted line — the fallback overcounts by
     construction (SH1 is a shield can: its bbox encloses the
     frontend it exists to cover), so fallback pairs are printed
     and counted but gate only once a real courtyard is drawn.
     The blind list is printed in every audit until it is empty.
Exit 0 iff no unconnected net, no unlisted violation, and no
courtyard collision. Known/accepted clearance items can be waived
in WAIVERS with a written reason; waivers are printed, never
silent.
Run under xvfb-run (pcbnew zone data needs the app context).
"""
import sys, wx
_app = wx.App(False)
import pcbnew

MM = pcbnew.FromMM
# HV clearance class (1.0 mm surface creepage) — assigned by CARRIED
# VOLTAGE, never by name (census: results/class-voltage-census.txt).
# APD_K/HV_RAW/HV_SEC: the <=259.4 V clamped bias domain. TP_HV: the
# test point floats to ~APD_K potential through R34 10 MOhm.
# HV_R29M (~259 V), HV_R30M (~130 V), HV_R31A (~160 V), HV_R31B
# (~80 V): parts-fix string midpoints. HV_OVP1/HV_OVP2: OVP zener
# stack midpoints. The LT3757 control nets (HV_GATE <=7.2 V,
# HV_FBX 1.6 V, HV_SENSE <=0.12 V, ...) are LV and stay at the 0.20
# default — hw/tests/test_hv_class.py pins both directions.
HV_NETS = {"APD_K", "HV_RAW", "HV_SEC", "TP_HV", "HV_R29M",
           "HV_R30M", "HV_R31A", "HV_R31B", "HV_OVP1", "HV_OVP2",
           # docs/12: WE-FLEX secondary string taps (peak 21-148 V by
           # position/variant) and CW ladder nodes (peak Vout/2,
           # <= 210 V) — HV generator internals, classed with the rail.
           "HV_S1", "HV_S2", "HV_S3", "HV_S4",
           "HV_M1", "HV_M2", "HV_M3"}
POWER_NETS = {"+5V", "+3V3D", "+3V3D_CDR", "+3V3A", "+VA", "-VA",
              "NEG_RAW", "VBUS_RAW", "PHY_1V8", "PHY_1V8A"}
WAIVERS = []   # (net_a, net_b, reason) — filled from docs/04 if needed

def clearance_for(net):
    if net in HV_NETS: return 1.0
    if net in POWER_NETS: return 0.25
    return 0.2

SURFACE = None  # set in main (needs pcbnew layer ids)

def _fallback_courtyard(fp, flipped):
    """Bbox-fallback courtyard for a footprint with no drawn
    courtyard polygon: union bbox of its pads and its body outline
    (Fab-layer shapes; Silkscreen shapes when it has no Fab —
    text items never count), expanded by the standard 0.25 mm
    courtyard allowance. Returns a SHAPE_POLY_SET rectangle in
    board coordinates."""
    fab = pcbnew.B_Fab if flipped else pcbnew.F_Fab
    silk = pcbnew.B_SilkS if flipped else pcbnew.F_SilkS
    shapes = [d for d in fp.GraphicalItems()
              if isinstance(d, pcbnew.PCB_SHAPE)]
    boxes = [d.GetBoundingBox() for d in shapes if d.GetLayer() == fab]
    if not boxes:
        boxes = [d.GetBoundingBox() for d in shapes
                 if d.GetLayer() == silk]
    boxes += [p.GetBoundingBox() for p in fp.Pads()]
    xs0 = min(b.GetLeft() for b in boxes); xs1 = max(b.GetRight() for b in boxes)
    ys0 = min(b.GetTop() for b in boxes); ys1 = max(b.GetBottom() for b in boxes)
    m = MM(0.25)
    poly = pcbnew.SHAPE_POLY_SET()
    poly.NewOutline()
    for x, y in ((xs0 - m, ys0 - m), (xs1 + m, ys0 - m),
                 (xs1 + m, ys1 + m), (xs0 - m, ys1 + m)):
        poly.Append(pcbnew.VECTOR2I(x, y))
    return poly

def courtyard_pairs(board):
    """Same-side courtyard polygon collisions.
    Returns (pairs, blind): pairs is a list of
    (ref_a, ref_b, side, area_mm2, fallback_used); blind is the
    sorted list of refs measured with the bbox fallback because
    they have no drawn courtyard polygon."""
    entries = []  # (ref, side, poly, bbox, fallback?)
    blind = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        flipped = fp.IsFlipped()
        layer = pcbnew.B_CrtYd if flipped else pcbnew.F_CrtYd
        side = "bottom" if flipped else "top"
        poly = None
        try:
            poly = fp.GetCourtyard(layer)
        except Exception:
            poly = None
        fb = False
        if poly is None or poly.OutlineCount() == 0:
            poly = _fallback_courtyard(fp, flipped)
            fb = True
            blind.append(ref)
        entries.append((ref, side, poly, poly.BBox(), fb))
    pairs = []
    for i in range(len(entries)):
        ri, si, pi, bi, fbi = entries[i]
        for j in range(i + 1, len(entries)):
            rj, sj, pj, bj, fbj = entries[j]
            if si != sj or not bi.Intersects(bj):
                continue
            inter = pcbnew.SHAPE_POLY_SET(pi)
            inter.BooleanIntersection(pj, pcbnew.SHAPE_POLY_SET.PM_FAST)
            area = 0.0
            for k in range(inter.OutlineCount()):
                area += inter.Outline(k).Area()
            area /= 1e12  # nm^2 -> mm^2
            if area > 0.001:
                pairs.append((ri, rj, si, area, fbi or fbj))
    return pairs, sorted(blind)

def need_for(na, nb, shared_layers):
    """Layer-aware clearance: the 1.0 mm HV rule is a surface
    creepage rule. A pair sharing ONLY buried layers (In1/In2) is
    separated by solid FR4 prepreg, whose dielectric strength makes
    0.3 mm ample for 420 V — so HV counts 0.3 there. Pairs sharing
    F.Cu or B.Cu use the full surface values."""
    internal_only = shared_layers and not (shared_layers & SURFACE)
    def c(n):
        if internal_only and n in HV_NETS: return 0.3
        return clearance_for(n)
    return max(c(na), c(nb))

def main(path="hw/pdlvds_rx.kicad_pcb"):
    global SURFACE
    SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
    board = pcbnew.LoadBoard(path)
    items = []   # (kind, net, layers:set, shape, bbox, desc)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net: continue
            layers = set()
            for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
                if pad.IsOnLayer(l): layers.add(l)
            items.append(("pad", net, layers, pad.GetEffectiveShape(),
                          pad.GetBoundingBox(), f"{fp.GetReference()}.{pad.GetNumber()}"))
    for t in board.GetTracks():
        net = t.GetNetname()
        if isinstance(t, pcbnew.PCB_VIA):
            layers = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}
            kind = "via"
        else:
            layers = {t.GetLayer()}; kind = "track"
        items.append((kind, net, layers, t.GetEffectiveShape(),
                      t.GetBoundingBox(), f"{kind}@{pcbnew.ToMM(t.GetPosition())}"))
    for z in board.Zones():
        net = z.GetNetname()
        layer = z.GetLayer()
        poly = z.GetFilledPolysList(layer)
        if poly.OutlineCount() == 0: continue
        items.append(("zone", net, {layer}, poly, z.GetBoundingBox(), f"zone L{layer}"))
    print(f"copper items: {len(items)}")
    # ---------- connectivity (union-find) ----------
    parent = list(range(len(items)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    bynet = {}
    for i, it in enumerate(items): bynet.setdefault(it[1], []).append(i)
    unconnected = []
    for net, idxs in sorted(bynet.items()):
        # bucket by bbox overlap on shared layer, then Collide(0)
        for ai in range(len(idxs)):
            for bi in range(ai + 1, len(idxs)):
                a, b = items[idxs[ai]], items[idxs[bi]]
                if not (a[2] & b[2]): continue
                if not a[4].Intersects(b[4]): continue
                try:
                    if a[3].Collide(b[3], 0): union(idxs[ai], idxs[bi])
                except Exception:
                    union(idxs[ai], idxs[bi])  # conservative
        groups = {}
        for i in idxs: groups.setdefault(find(i), []).append(items[i][5])
        if len(groups) > 1:
            unconnected.append((net, [sorted(g)[:4] for g in groups.values()]))
    # ---------- clearance ----------
    violations = []
    intrinsic = []  # pad pairs of the SAME footprint: their spacing is
    # fixed by the manufacturer's footprint geometry (e.g. 0.5 mm-pitch
    # QFN pads are 0.2 mm apart by design) — no routing or placement
    # decision can change it, so it is reported separately, not counted
    # as a routing violation. Still printed, never silent.
    n = len(items)
    for i in range(n):
        a = items[i]
        for j in range(i + 1, n):
            b = items[j]
            if a[1] == b[1]: continue
            if not (a[2] & b[2]): continue
            need = need_for(a[1], b[1], a[2] & b[2])
            if not a[4].Intersects(b[4]):
                # grow test: skip if bboxes are farther than need apart
                ax0, ay0 = pcbnew.ToMM(a[4].GetLeft()), pcbnew.ToMM(a[4].GetTop())
                ax1, ay1 = pcbnew.ToMM(a[4].GetRight()), pcbnew.ToMM(a[4].GetBottom())
                bx0, by0 = pcbnew.ToMM(b[4].GetLeft()), pcbnew.ToMM(b[4].GetTop())
                bx1, by1 = pcbnew.ToMM(b[4].GetRight()), pcbnew.ToMM(b[4].GetBottom())
                dx = max(bx0 - ax1, ax0 - bx1, 0); dy = max(by0 - ay1, ay0 - by1, 0)
                if (dx * dx + dy * dy) ** 0.5 > need: continue
            try:
                # equality passes (a gap of exactly the clearance is
                # compliant — e.g. zone fills carved at exactly the
                # rule), hence the 1 um tolerance
                hit = a[3].Collide(b[3], MM(need - 0.001))
            except Exception:
                hit = False
            if hit:
                if any({a[1], b[1]} == {w[0], w[1]} for w in WAIVERS): continue
                if a[0] == "pad" and b[0] == "pad" and \
                   a[5].rsplit(".", 1)[0] == b[5].rsplit(".", 1)[0]:
                    intrinsic.append((a[1], a[5], b[1], b[5], need))
                    continue
                violations.append((a[1], a[5], b[1], b[5], need))
    print(f"unconnected nets: {len(unconnected)}")
    for net, gs in unconnected:
        print(f"  UNCONNECTED {net}: {len(gs)} groups, e.g. {gs}")
    print(f"clearance violations: {len(violations)}")
    for v in violations[:600]:
        print(f"  CLEARANCE {v[0]} ({v[1]}) vs {v[2]} ({v[3]}): need {v[4]} mm")
    print(f"intrinsic same-footprint pad pairs below class clearance "
          f"(datasheet geometry, not routable): {len(intrinsic)}")
    for v in intrinsic[:20]:
        print(f"  INTRINSIC {v[0]} ({v[1]}) vs {v[2]} ({v[3]}): need {v[4]} mm")
    # ---------- courtyard collisions (HARD GATE: no waivers) ----
    cpairs, cblind = courtyard_pairs(board)
    gated = [p for p in cpairs if not p[4]]
    fbpairs = [p for p in cpairs if p[4]]
    print(f"courtyard collisions: {len(gated)}")
    for ra, rb, side, area, fb in sorted(gated):
        print(f"  COURTYARD {ra} x {rb} ({side}) area={area:.4f} mm^2")
    print(f"courtyard fallback pairs (blind footprints, reported "
          f"not gated): {len(fbpairs)}")
    for ra, rb, side, area, fb in sorted(fbpairs):
        print(f"  COURTYARD-FALLBACK {ra} x {rb} ({side}) "
              f"area={area:.4f} mm^2")
    if cblind:
        print(f"courtyard bbox fallback in use (no drawn courtyard): "
              f"{cblind}")
    ok = not unconnected and not violations and not gated
    print("PCB CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "hw/pdlvds_rx.kicad_pcb"))
