#!/usr/bin/env python3
"""t_ah12_cleanup2.py -- second surgical cleanup, on h7.

1. Restore two I2C_SCL B segs wrongly deleted as 'tail' in t_ah11:
   the SE junction is (77.375,9.125), not (77.875,8.625) -- the segs
   (77.375,9.125)->(77.625,8.875) and (77.625,8.875)->(77.875,8.625)
   are the southern chain itself. (The true tail was only the two
   segs west of (77.375,9.125), already removed.)
2. Delete groute's +3V3A via (75.5,8.75) -- placed 0.177 from the
   pre-existing staircase via (75.625,8.625) d0.8, drills overlap --
   and re-anchor its four segs onto the existing via:
     B   (73.625,10.625)->(75.625,8.625)   (was ->(75.5,8.75))
     B   (75.625,8.625)->(71.25,11.125)    (was (75.5,8.75)->)
     In2 (75.625,8.625)->(76.25,9.875)     (was (75.5,8.75)->)
     In2 (75.5,9.0)->(75.625,8.625)        (was ->(75.5,8.75))
All adds gated against the post-deletion exact item model.
Usage: t_ah12_cleanup2.py IN OUT
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

def find_via(net, p, dia, expect=1):
    out = []
    for t in b.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() != net:
            continue
        q = (mm(t.GetPosition().x), mm(t.GetPosition().y))
        if close(p, q) and abs(mm(t.GetWidth()) - dia) < 0.01:
            out.append(t)
    assert len(out) == expect, (net, p, len(out))
    return out

victims = []
victims += find_via('+3V3A', (75.5, 8.75), 0.5)
victims += find_seg('+3V3A', B, (73.625, 10.625), (75.5, 8.75))
victims += find_seg('+3V3A', B, (75.5, 8.75), (71.25, 11.125))
victims += find_seg('+3V3A', IN2, (75.5, 8.75), (76.25, 9.875))
victims += find_seg('+3V3A', IN2, (75.5, 9.0), (75.5, 8.75))
print(f'victims: {len(victims)} (expect 5)')
assert len(victims) == 5
for t in victims:
    b.Remove(t)

items, _ = repair.build_items(b)
NEW = [('+3V3A', B, (73.625, 10.625), (75.625, 8.625), 0.2),
       ('+3V3A', B, (75.625, 8.625), (71.25, 11.125), 0.2),
       ('+3V3A', IN2, (75.625, 8.625), (75.8, 9.2), 0.2),
       ('+3V3A', IN2, (75.8, 9.2), (76.25, 9.875), 0.2),
       ('+3V3A', IN2, (75.5, 9.0), (75.625, 8.625), 0.2),
       ('I2C_SCL', B, (77.375, 9.125), (77.625, 8.875), 0.25),
       ('I2C_SCL', B, (77.625, 8.875), (77.875, 8.625), 0.25)]

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

b0 = pcbnew.LoadBoard(SRC)
b2 = pcbnew.LoadBoard(OUT)
for net in ('+3V3A', 'I2C_SCL'):
    n0 = sum(1 for t in b0.GetTracks() if t.GetNetname() == net)
    n1 = sum(1 for t in b2.GetTracks() if t.GetNetname() == net)
    print(f'{net}: {n0} -> {n1} (delta {n1 - n0:+d})')
