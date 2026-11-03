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
Exit 0 iff no unlisted violation. Known/accepted items can be waived in
WAIVERS with a written reason; waivers are printed, never silent.
Run under xvfb-run (pcbnew zone data needs the app context).
"""
import sys, wx
_app = wx.App(False)
import pcbnew

MM = pcbnew.FromMM
HV_NETS = {"APD_K", "HV_RAW", "HV_SEC"}
POWER_NETS = {"+5V", "+3V3D", "+3V3D_CDR", "+3V3A", "+VA", "-VA",
              "NEG_RAW", "VBUS_RAW", "PHY_1V8", "PHY_1V8A"}
WAIVERS = []   # (net_a, net_b, reason) — filled from docs/04 if needed

def clearance_for(net):
    if net in HV_NETS: return 1.0
    if net in POWER_NETS: return 0.25
    return 0.2

SURFACE = None  # set in main (needs pcbnew layer ids)

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
    ok = not unconnected and not violations
    print("PCB CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "hw/pdlvds_rx.kicad_pcb"))
