"""t_ai10: joint via-position optimizer for +3V3A U7.25 + PHY_1V8
south fanout re-lay, over the ripB board (PHY fanout ripped).
Variables: PHY via P (d0.5) + F stub template (south leg at x77.25,
east leg at y=py, w0.2); U7.25 via Q (d0.5) + straight F stub w0.2.
Onward legs checked by grid floods over the exact item model:
PHY on B (w0.6) from P to the kept B run y16.2; +3V3A on In2 (w0.6)
from Q to the staircase joint (77.375,13.125). All margins exact."""
import math, sys
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pair_clr, pt_margin, seg_margin

SRC = 'scratch/work/ai/ripB.kicad_pcb'
items, pools = load_items(SRC)
F, I2, B = 0, 1, 2


def pool(li, x0, x1, y0, y1, pad=1.2):
    return [it for it in items[li]
            if not (it[3] and False) and
            _near(it, x0 - pad, x1 + pad, y0 - pad, y1 + pad)]


def _near(it, x0, x1, y0, y1):
    d = it[2]
    if it[0] == 'seg':
        return not (max(d[0][0], d[1][0]) < x0 or
                    min(d[0][0], d[1][0]) > x1 or
                    max(d[0][1], d[1][1]) < y0 or
                    min(d[0][1], d[1][1]) > y1)
    if it[0] == 'via':
        return x0 <= d[0] <= x1 and y0 <= d[1] <= y1
    return x0 <= d[0] + d[2] and d[0] - d[2] <= x1 and \
        y0 <= d[1] + d[3] and d[1] - d[3] <= y1


PF = pool(F, 76.5, 79.0, 9.5, 12.2)
PI = pool(I2, 76.5, 79.0, 9.5, 12.2)
PB = pool(B, 76.5, 79.0, 9.5, 12.2)
ALL = {F: PF, I2: PI, B: PB}


def via_gates(net, pt, rad, extra=()):
    worst = 9.9
    for li in (F, I2, B):
        m, _ = pt_margin(pt, rad, net, items[li], li)
        worst = min(worst, m)
    for (net2, pt2, rad2) in extra:
        d = math.dist(pt, pt2) - rad - rad2 - pair_clr(net, net2)
        worst = min(worst, d)
    return worst


def seg_gate(net, a, b, li, hw, extra_segs=(), extra_vias=()):
    m, _ = seg_margin(a, b, hw, net, items[li], li)
    worst = m
    for (n2, a2, b2, hw2) in extra_segs:
        # seg-seg centreline distance minus half widths minus clr
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
pairs = []
for (P, ps) in Ps:
    for (Q, qs) in Qs:
        if math.dist(P, Q) < 0.25 + 0.25 + 0.2:
            continue
        # PHY stub vs Q
        g1 = seg_gate('PHY_1V8', PHY_PAD, (77.25, P[1]), F, 0.1,
                      extra_vias=(('+3V3A', Q, 0.25),))
        g2 = seg_gate('PHY_1V8', (77.25, P[1]), P, F, 0.1,
                      extra_vias=(('+3V3A', Q, 0.25),))
        # U7.25 stub vs P
        g3 = seg_gate('+3V3A', A25_PAD, Q, F, 0.1,
                      extra_vias=(('PHY_1V8', P, 0.25),))
        # stub vs stub
        g4 = _ss(PHY_PAD, (77.25, P[1]), A25_PAD, Q) - 0.1 - 0.1 - 0.2
        g5 = _ss((77.25, P[1]), P, A25_PAD, Q) - 0.1 - 0.1 - 0.2
        w = min(ps, qs, g1, g2, g3, g4, g5)
        if w >= 0:
            pairs.append((w, P, Q))
pairs.sort(reverse=True)
print(f'pairs passing via/stub gates: {len(pairs)}')
for w, P, Q in pairs[:10]:
    print(f'   worst {w:+.3f}  P={P}  Q={Q}')
