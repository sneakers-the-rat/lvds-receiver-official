"""t_ai12: joint optimizer v3 (fine grid + onward gates) for +3V3A U7.25 + PHY_1V8 re-lay.
Options carry (via point, radius, stub seg list, static worst margin):
 PHY: d0.5 grid vias with diagonal stub (elbow on x77.25 at
      ey in {10.812, 10.95, 11.1}), or the original d0.8 home
      (77.875,10.375) with its original 3-seg stub.
 U7.25: d0.5 grid vias (wider box) with straight or L-south stub.
Pair gates: via-via, stub-vs-other-via, stub-vs-stub (all F, w0.2)."""
import math, sys
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import (load_items, pair_clr, pt_margin, seg_margin,
                      in_box_pool)

items = load_items(pcbnew.LoadBoard('scratch/work/ai/ripB.kicad_pcb'))
F, I2, B = 0, 1, 2
POOLS = in_box_pool(items, (76.0, 79.6, 9.0, 12.6), pad=1.2)


def _ps(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx +
                                         (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _seg_int(a, b, c, d):
    def o(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-12 else (1 if v > 0 else -1)
    return o(a, b, c) != o(a, b, d) and o(c, d, a) != o(c, d, b)


def _ss(a, b, c, d):
    if _seg_int(a, b, c, d):
        return 0.0
    return min(_ps(a, c, d), _ps(b, c, d), _ps(c, a, b), _ps(d, a, b))


def via_static(net, pt, rad):
    w = 9.9
    for li in (F, I2, B):
        m, _ = pt_margin(li, pt[0], pt[1], net, rad, POOLS[li])
        w = min(w, m)
    return w


def stub_static(net, segs, hw=0.1):
    w = 9.9
    for (a, b) in segs:
        m, _ = seg_margin(F, a, b, net, hw, POOLS[F])
        w = min(w, m)
    return w


PHY_PAD = (77.25, 11.562)
A25_PAD = (77.75, 11.562)

Popts = []
# original home, d0.8, original stub
P0 = (77.875, 10.375)
stub0 = [(PHY_PAD, (77.25, 10.812)), ((77.25, 10.812), (77.625, 10.625)),
         ((77.625, 10.625), P0)]
w = min(via_static('PHY_1V8', P0, 0.4), stub_static('PHY_1V8', stub0))
Popts.append((P0, 0.4, stub0, w, 'orig d0.8'))
# grid d0.5, diagonal stubs
for ey in (10.75, 10.812, 10.875, 10.95, 11.1):
    py_ = 9.9
    while py_ <= 10.201:
        px = 77.65
        while px <= 77.951:
            pt = (round(px, 4), round(py_, 4))
            if pt == P0:
                px += 0.0625
                continue
            stub = [(PHY_PAD, (77.25, ey)), ((77.25, ey), pt)]
            w = min(via_static('PHY_1V8', pt, 0.25),
                    stub_static('PHY_1V8', stub))
            if w >= 0:
                Popts.append((pt, 0.25, stub, w, f'diag ey{ey}'))
            px += 0.03125
        py_ += 0.03125
print(f'P options: {len(Popts)} '
      f'(orig w={Popts[0][3]:+.3f})')

Qopts = []
qy = 10.7
while qy <= 11.001:
    qx = 77.8
    while qx <= 78.051:
        pt = (round(qx, 4), round(qy, 4))
        for name, stub in (
                ('straight', [(A25_PAD, pt)]),
                ('Lsouth', [(A25_PAD, (77.75, pt[1])),
                            ((77.75, pt[1]), pt)])):
            w = min(via_static('+3V3A', pt, 0.25),
                    stub_static('+3V3A', stub))
            if w >= 0:
                Qopts.append((pt, 0.25, stub, w, name))
        qx += 0.03125
    qy += 0.03125
print(f'Q options: {len(Qopts)}')

rows = []
for (P, prad, pstub, pw, pname) in Popts:
    for (Q, qrad, qstub, qw, qname) in Qopts:
        gs = {}
        gs['vv'] = math.dist(P, Q) - prad - qrad - 0.2
        gs['w0'] = min(pw, qw)
        worst = min(gs['vv'], gs['w0'])
        if worst < -0.4:
            continue
        for (a, b) in pstub:
            d = _ps(Q, a, b) - qrad - 0.1 - 0.2
            worst = min(worst, d)
        for (a, b) in qstub:
            d = _ps(P, a, b) - prad - 0.1 - 0.2
            worst = min(worst, d)
        for (a, b) in pstub:
            for (c, d2) in qstub:
                dd = _ss(a, b, c, d2) - 0.1 - 0.1 - 0.2
                worst = min(worst, dd)
        rows.append((worst, P, prad, pname, Q, qname))
rows.sort(key=lambda r: -r[0])


def onward(P, Q):
    # PHY B path (w0.6): P -> (78.75,P.y-0.14) -> (78.75,15.5)
    #   -> (77.8,16.2) corner of the kept B run
    pathB = [(P, (78.75, round(P[1] - 0.14, 4))),
             ((78.75, round(P[1] - 0.14, 4)), (78.75, 15.5)),
             ((78.75, 15.5), (77.8, 16.2))]
    w = 9.9
    for (a, b) in pathB:
        m, _ = seg_margin(B, a, b, 'PHY_1V8', 0.3,
                          in_box_pool(items, (76.5, 79.6, 9.0, 17.0),
                                      pad=1.2)[B])
        w = min(w, m)
        d = _ps(Q, a, b) - 0.25 - 0.3 - 0.25
        w = min(w, d)
    # +3V3A In2 path (w0.6): Q -> (Q.x,12.0) -> (77.375,13.125)
    pathI = [(Q, (Q[0], 12.0)), ((Q[0], 12.0), (77.375, 13.125))]
    for (a, b) in pathI:
        m, _ = seg_margin(I2, a, b, '+3V3A', 0.3,
                          in_box_pool(items, (76.5, 79.0, 10.0, 14.0),
                                      pad=1.2)[I2])
        w = min(w, m)
        d = _ps(P, a, b) - 0.25 - 0.3 - 0.25
        w = min(w, d)
    return w, pathB, pathI


print(f'pairs scored: {len(rows)}; onward-gating top 25:')
done = 0
for w, P, prad, pname, Q, qname in rows[:25]:
    ow, pathB, pathI = onward(P, Q)
    print(f'   stub {w:+.3f} onward {ow:+.3f}  P={P} [{pname}]  '
          f'Q={Q} [{qname}]')
    done += 1
for w, P, prad, pname, Q, qname in rows[:10]:
    print(f'   worst {w:+.3f}  P={P} r{prad} [{pname}]  '
          f'Q={Q} [{qname}]')
