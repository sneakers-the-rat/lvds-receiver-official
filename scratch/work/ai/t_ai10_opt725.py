"""t_ai10: joint via-position optimizer for +3V3A U7.25 + PHY_1V8
south fanout re-lay, over the ripB board (PHY fanout ripped).
Variables: PHY via P (d0.5) + F stub template (south leg at x77.25,
east leg at y=py, w0.2); U7.25 via Q (d0.5) + straight F stub w0.2.
Onward legs checked by grid floods over the exact item model:
PHY on B (w0.6) from P to the kept B run y16.2; +3V3A on In2 (w0.6)
from Q to the staircase joint (77.375,13.125). All margins exact."""
import math, sys
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import (load_items, pair_clr, pt_margin,
                      seg_margin, in_box_pool)

SRC = 'scratch/work/ai/ripB.kicad_pcb'
import wx
_app = wx.App(False)
import pcbnew
items = load_items(pcbnew.LoadBoard(SRC))
F, I2, B = 0, 1, 2


POOLS = in_box_pool(items, (76.0, 79.5, 9.0, 12.6), pad=1.2)


def via_gates(net, pt, rad, extra=()):
    worst = 9.9
    for li in (F, I2, B):
        m, _ = pt_margin(li, pt[0], pt[1], net, rad, POOLS[li])
        worst = min(worst, m)
    for (net2, pt2, rad2) in extra:
        d = math.dist(pt, pt2) - rad - rad2 - pair_clr(net, net2)
        worst = min(worst, d)
    return worst


def seg_gate(net, a, b, li, hw, extra_segs=(), extra_vias=()):
    m, _ = seg_margin(li, a, b, net, hw, POOLS[li])
    worst = m
    for (n2, a2, b2, hw2) in extra_segs:
        d = _ss(a, b, a2, b2) - hw - hw2 - pair_clr(net, n2)
        worst = min(worst, d)
    for (n2, pt2, rad2) in extra_vias:
        d = _ps(pt2, a, b) - rad2 - hw - pair_clr(net, n2)
        worst = min(worst, d)
    return worst


def _ps(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx +
                                         (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _ss(a, b, c, d):
    if _seg_int(a, b, c, d):
        return 0.0
    return min(_ps(a, c, d), _ps(b, c, d), _ps(c, a, b), _ps(d, a, b))


def _seg_int(a, b, c, d):
    def o(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-12 else (1 if v > 0 else -1)
    return o(a, b, c) != o(a, b, d) and o(c, d, a) != o(c, d, b)


PHY_PAD = (77.25, 11.562)
A25_PAD = (77.75, 11.562)

# --- candidate P (PHY via) ---
Ps = []
py_ = 9.7
while py_ <= 10.951:
    px = 77.3
    while px <= 78.351:
        pt = (round(px, 4), round(py_, 4))
        if via_gates('PHY_1V8', pt, 0.25) >= 0:
            s1 = seg_gate('PHY_1V8', PHY_PAD, (77.25, pt[1]), F, 0.1)
            s2 = seg_gate('PHY_1V8', (77.25, pt[1]), pt, F, 0.1)
            if s1 >= 0 and s2 >= 0:
                Ps.append((pt, min(s1, s2)))
        px += 0.0625
    py_ += 0.0625
print(f'P candidates: {len(Ps)}')

# --- candidate Q (U7.25 via) ---
Qs = []
qy = 10.55
while qy <= 11.351:
    qx = 77.45
    while qx <= 78.051:
        pt = (round(qx, 4), round(qy, 4))
        if via_gates('+3V3A', pt, 0.25) >= 0:
            s = seg_gate('+3V3A', A25_PAD, pt, F, 0.1)
            if s >= 0:
                Qs.append((pt, s))
        qx += 0.0625
    qy += 0.0625
print(f'Q candidates: {len(Qs)}')

# --- pairs ---
rows = []
for (P, ps) in Ps:
    for (Q, qs) in Qs:
        dvv = math.dist(P, Q) - 0.25 - 0.25 - 0.2
        g1 = seg_gate('PHY_1V8', PHY_PAD, (77.25, P[1]), F, 0.1,
                      extra_vias=(('+3V3A', Q, 0.25),))
        g2 = seg_gate('PHY_1V8', (77.25, P[1]), P, F, 0.1,
                      extra_vias=(('+3V3A', Q, 0.25),))
        g3 = seg_gate('+3V3A', A25_PAD, Q, F, 0.1,
                      extra_vias=(('PHY_1V8', P, 0.25),))
        g4 = _ss(PHY_PAD, (77.25, P[1]), A25_PAD, Q) - 0.1 - 0.1 - 0.2
        g5 = _ss((77.25, P[1]), P, A25_PAD, Q) - 0.1 - 0.1 - 0.2
        gs = {'vv': dvv, 'stubS-Q': g1, 'stubE-Q': g2, 'stub25-P': g3,
              'ss1': g4, 'ss2': g5, 'Pstub': ps, 'Qstub': qs}
        rows.append((min(gs.values()), P, Q, gs))
rows.sort(key=lambda r: -r[0])
print(f'pairs total: {len(rows)}')
for w, P, Q, gs in rows[:8]:
    bad = {k: round(v, 3) for k, v in gs.items() if v < 0.05}
    print(f'   worst {w:+.3f}  P={P}  Q={Q}  tight: {bad}')
