#!/usr/bin/env python3
"""Measure TRUE gaps for the audit's violating pairs on the v4 board."""
import sys, wx
_app = wx.App(False)
import pcbnew

MM = pcbnew.FromMM
HV_NETS = {"APD_K", "HV_RAW", "HV_SEC"}
POWER_NETS = {"+5V", "+3V3D", "+3V3D_CDR", "+3V3A", "+VA", "-VA",
              "NEG_RAW", "VBUS_RAW", "PHY_1V8", "PHY_1V8A"}

def clearance_for(net):
    if net in HV_NETS: return 1.0
    if net in POWER_NETS: return 0.25
    return 0.2

board = pcbnew.LoadBoard('hw/pdlvds_rx.kicad_pcb')
items = []
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
    net = z.GetNetname(); layer = z.GetLayer()
    poly = z.GetFilledPolysList(layer)
    if poly.OutlineCount() == 0: continue
    items.append(("zone", net, {layer}, poly, z.GetBoundingBox(), f"zone L{layer}"))

def true_gap(a, b):
    lo, hi = 0.0, 2.0
    if not a[3].Collide(b[3], MM(hi)): return hi
    for _ in range(24):
        mid = (lo + hi) / 2
        if a[3].Collide(b[3], MM(mid)): hi = mid
        else: lo = mid
    return lo

n = len(items)
viol = []
for i in range(n):
    a = items[i]
    for j in range(i + 1, n):
        b = items[j]
        if a[1] == b[1] or not (a[2] & b[2]): continue
        need = max(clearance_for(a[1]), clearance_for(b[1]))
        if not a[4].Intersects(b[4]):
            ax0, ay0 = pcbnew.ToMM(a[4].GetLeft()), pcbnew.ToMM(a[4].GetTop())
            ax1, ay1 = pcbnew.ToMM(a[4].GetRight()), pcbnew.ToMM(a[4].GetBottom())
            bx0, by0 = pcbnew.ToMM(b[4].GetLeft()), pcbnew.ToMM(b[4].GetTop())
            bx1, by1 = pcbnew.ToMM(b[4].GetRight()), pcbnew.ToMM(b[4].GetBottom())
            dx = max(bx0 - ax1, ax0 - bx1, 0); dy = max(by0 - ay1, ay0 - by1, 0)
            if (dx * dx + dy * dy) ** 0.5 > need: continue
        try:
            if a[3].Collide(b[3], MM(need)):
                viol.append((a, b, need))
        except Exception:
            pass

print(f"violating pairs: {len(viol)}")
zone_pairs = [v for v in viol if v[0][0] == 'zone' or v[1][0] == 'zone']
print(f"  involving zone fills: {len(zone_pairs)}")
routed = [v for v in viol if v[0][0] != 'zone' and v[1][0] != 'zone']
same_fp = [v for v in routed if v[0][0] == 'pad' and v[1][0] == 'pad'
           and v[0][5].rsplit('.', 1)[0] == v[1][5].rsplit('.', 1)[0]]
print(f"  same-footprint pad pairs: {len(same_fp)}")
rest = [v for v in routed if v not in same_fp]
print(f"  routed-copper pairs: {len(rest)}")
import collections
hist = collections.Counter()
worst = []
for a, b, need in rest:
    g = true_gap(a, b)
    hist[round(g * 20) / 20] += 1
    worst.append((g, need, a[1], a[5], b[1], b[5]))
print("  true-gap histogram (0.05 bins):", sorted(hist.items()))
worst.sort()
print("  12 worst routed-copper gaps:")
for g, need, na, da, nb, db in worst[:12]:
    print(f"    gap={g:.3f} need={need}  {na} ({da}) vs {nb} ({db})")
