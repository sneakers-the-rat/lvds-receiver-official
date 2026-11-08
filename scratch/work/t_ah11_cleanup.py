#!/usr/bin/env python3
"""t_ah11_cleanup.py -- surgical cleanup of the groute chain board (h6).

Fixes, all identified from DRC + step diffs:
  A. delete ONE of each stacked duplicate via pair:
     +3V3A (75.5,8.75), +3V3A (78.625,16.75)
  B. delete +3V3A via (73.875,10.5) (drill overlaps existing (73.625,10.625)
     d0.8) + its F seg (74.25,10.625)->(73.875,10.5); re-lay its B seg
     from the EXISTING via: B (73.625,10.625)->(75.5,8.75)   [gated]
  C. SCL: delete via (69.5,12.75) (0.177 from existing (69.625,12.625));
     re-lay B seg start onto the existing via:
     B (69.625,12.625)->(65.0,12.5)                          [gated]
     delete via (69.25,1.375) (0.125 from existing (69.375,1.375));
     re-lay F seg (69.375,1.375)->(67.875,1.625)             [gated]
     re-lay B seg (68.875,1.625)->(69.375,1.375)             [gated]
  D. delete SCL B west tail (6 segs, via (69.625,12.625) east chain --
     dangling after the rip; the via stays, fed by its F stub)
  E. delete SCL B SE tail (4 segs west of junction (77.875,8.625))
  F. delete +3V3A In2 staircase lower 7 segs (orphaned by the rip;
     U7.16 rejoined via the northern web); KEEP the top seg and add
     In2 joiner (77.375,13.125)->(77.125,13.125) so the top seg lands
     on h5's In2 path                                  [joiner gated]
Netcodes captured BEFORE any Remove. Deletions are exact-match and
asserted. Reload census asserts per-net deltas.
Usage: t_ah11_cleanup.py IN OUT
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

SRC, OUT = sys.argv[1], sys.argv[2]
F, IN2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
LN = {F: 0, IN2: 1, B: 2}

b = pcbnew.LoadBoard(SRC)
codes = {n: b.GetNetcodeFromNetname(n) for n in ('+3V3A', 'I2C_SCL')}
assert all(v >= 0 for v in codes.values())

def mm(v):
    return round(v / 1e6, 4)

def close(p, q):
    return abs(p[0] - q[0]) <= 0.002 and abs(p[1] - q[1]) <= 0.002

def find_seg(net, lay, a, c, expect=1):
    out = []
    for t in b.GetTracks():
        if t.Type() != pcbnew.PCB_TRACE_T or t.GetNetname() != net:
            continue
        if t.GetLayer() != lay:
            continue
        p = (mm(t.GetStart().x), mm(t.GetStart().y))
        q = (mm(t.GetEnd().x), mm(t.GetEnd().y))
        if (close(p, a) and close(q, c)) or (close(p, c) and close(q, a)):
            out.append(t)
    assert len(out) == expect, (net, lay, a, c, len(out))
    return out

def find_via(net, p, dia=None):
    out = []
    for t in b.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() != net:
            continue
        q = (mm(t.GetPosition().x), mm(t.GetPosition().y))
        if close(p, q) and (dia is None or abs(mm(t.GetWidth()) - dia) < 0.01):
            out.append(t)
    return out

victims = []
# A: one of each stacked pair
for net, p in (('+3V3A', (75.5, 8.75)), ('+3V3A', (78.625, 16.75))):
    vs = find_via(net, p, 0.5)
    assert len(vs) == 2, (net, p, len(vs))
    victims.append(vs[0])
# B: bad via + its F seg (keep its B seg for re-lay: delete + re-add)
vs = find_via('+3V3A', (73.875, 10.5), 0.5)
assert len(vs) == 1
victims += vs
victims += find_seg('+3V3A', F, (74.25, 10.625), (73.875, 10.5))
victims += find_seg('+3V3A', B, (73.875, 10.5), (75.5, 8.75))
# C: SCL duplicate vias + their segs (re-added below)
vs = find_via('I2C_SCL', (69.5, 12.75), 0.5)
assert len(vs) == 1
victims += vs
victims += find_seg('I2C_SCL', IN2, (69.5, 12.75), (65.0, 12.5))
vs = find_via('I2C_SCL', (69.25, 1.375), 0.5)
assert len(vs) == 1
victims += vs
victims += find_seg('I2C_SCL', F, (69.25, 1.375), (67.875, 1.625))
victims += find_seg('I2C_SCL', IN2, (68.875, 1.625), (69.25, 1.375))
# D: SCL B west tail
for a, c in (((69.625, 12.625), (69.875, 12.375)),
             ((69.875, 12.375), (70.125, 12.125)),
             ((70.125, 12.125), (70.375, 11.875)),
             ((70.375, 11.875), (70.625, 11.875)),
             ((70.625, 11.875), (70.875, 11.625)),
             ((70.875, 11.625), (72.875, 11.625))):
    victims += find_seg('I2C_SCL', B, a, c)
# E: SCL B SE tail
for a, c in (((76.875, 9.625), (77.125, 9.375)),
             ((77.125, 9.375), (77.375, 9.125)),
             ((77.375, 9.125), (77.625, 8.875)),
             ((77.625, 8.875), (77.875, 8.625))):
    victims += find_seg('I2C_SCL', B, a, c)
# F: +3V3A staircase lower 7 segs
for a, c in (((77.375, 13.125), (77.125, 12.875)),
             ((77.125, 12.875), (76.875, 12.625)),
             ((76.875, 12.625), (76.625, 12.375)),
             ((76.625, 12.375), (76.375, 12.125)),
             ((76.375, 12.125), (76.125, 11.875)),
             ((76.125, 11.875), (75.875, 11.625)),
             ((75.875, 11.625), (75.625, 11.375))):
    victims += find_seg('+3V3A', IN2, a, c)

expect = 2 + 3 + 5 + 6 + 4 + 7
print(f'victims: {len(victims)} (expect {expect})')
assert len(victims) == expect
for t in victims:
    b.Remove(t)

# gate the re-laid segs + joiner against the post-deletion model
items, _ = repair.build_items(b)
NEW = [('+3V3A', B, (73.625, 10.625), (75.5, 8.75), 0.2),
       ('I2C_SCL', IN2, (69.625, 12.625), (65.0, 12.5), 0.2),
       ('I2C_SCL', F, (69.375, 1.375), (67.875, 1.625), 0.2),
       ('I2C_SCL', IN2, (68.875, 1.625), (69.375, 1.375), 0.2),
       ('+3V3A', IN2, (77.375, 13.125), (77.125, 13.125), 0.2)]

def gate(net, li, a, c, w):
    def clr(o):
        return max(netclass(net)[1], netclass(o)[1] if o else 0.2)
    worst = (1e9, None, None)
    n = max(2, int(math.hypot(c[0] - a[0], c[1] - a[1]) / 0.05) + 1)
    for s in range(n + 1):
        x = a[0] + (c[0] - a[0]) * s / n
        y = a[1] + (c[1] - a[1]) * s / n
        for it in items[li].near(li, x, y):
            if it[1] == net:
                continue
            m = dist_to_item(it, x, y) - (w / 2 + clr(it[1]))
            if m < worst[0]:
                worst = (m, it, (round(x, 3), round(y, 3)))
    return worst

ok = True
for net, lay, a, c, w in NEW:
    m, it, at = gate(net, LN[lay], a, c, w)
    print(f'gate {net} {a}->{c}: {m:+.3f} vs {it[1] if it else None} at {at}')
    ok &= m >= 0
assert ok, 'gate failure -- aborting, nothing saved'

for net, lay, a, c, w in NEW:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(c[0]), pcbnew.FromMM(c[1])))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(lay)
    t.SetNetCode(codes[net])
    b.Add(t)
b.Save(OUT)
print('saved', OUT)

b2 = pcbnew.LoadBoard(OUT)
for net in ('+3V3A', 'I2C_SCL'):
    n0 = sum(1 for t in pcbnew.LoadBoard(SRC).GetTracks()
             if t.GetNetname() == net)
    n1 = sum(1 for t in b2.GetTracks() if t.GetNetname() == net)
    print(f'{net}: {n0} -> {n1} (delta {n1 - n0:+d})')
