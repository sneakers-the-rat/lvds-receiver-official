"""t_ba19: C22 SE-family evaluation. Survey box x[78,86]
y[16.5,25] (all layers, item census by net), then gate
candidate sites: pad1 hop to PHY's NE copper -- via
(78.10,17.50) / F seg (77.25,17.19)->(78.10,17.50) -- and
pad2 GND via search. Also report XI arc items in the box
(the shift-pricing input)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp252.kicad_pcb')
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
print('--- census x[78,86] y[16.5,25] by net/layer ---')
cen = {}
for l in range(3):
    for it in pool[l]:
        cc = C(it)
        if 78 <= cc[0] <= 86 and 16.5 <= cc[1] <= 25:
            k = (it[1], LAYN[l], it[0])
            cen[k] = cen.get(k, 0) + 1
for k in sorted(cen):
    print('  ', k, cen[k])
print('--- XI items in the box (shift candidates) ---')
for l in range(3):
    for it in pool[l]:
        if it[1] != 'XI':
            continue
        cc = C(it)
        if 78 <= cc[0] <= 86 and 16.5 <= cc[1] <= 25:
            d = it[2]
            if it[0] == 'seg':
                print(f'  {LAYN[l]} seg ({d[0]:.2f},{d[1]:.2f})->'
                      f'({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')
            elif it[0] == 'via':
                print(f'  {LAYN[l]} via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}')


def _near(l, x, y, r):
    return [o for o in pool[l]
            if abs(C(o)[0] - x) < r and abs(C(o)[1] - y) < r]


def gate_track(l, net, x1, y1, x2, y2, hw=0.10):
    it = ('seg', net, (x1, y1, x2, y2, hw), 0.25 if net == 'PHY_1V8' else 0.2)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    import math as _m
    r = _m.hypot(x2 - x1, y2 - y1) / 2 + 3.0
    worst, wo = 9.9, None
    for o in _near(l, mx, my, r):
        if o[1] == net:
            continue
        m = item_margin(l, it, [o])
        if m < worst:
            worst, wo = m, o[1]
    return worst, wo


def gate_via(x, y, net):
    it = ('via', net, (x, y, 0.25), 0.2)
    worst, wo = 9.9, None
    for l in range(3):
        for o in _near(l, x, y, 3.0):
            if o[1] == net:
                continue
            m = item_margin(l, it, [o])
            if m < worst:
                worst, wo = m, (LAYN[l], o[1])
    return worst, wo


def pads(cx, cy, rot):
    if rot == 0:
        return (cx - 0.48, cy), (cx + 0.48, cy)
    if rot == 180:
        return (cx + 0.48, cy), (cx - 0.48, cy)
    if rot == 90:
        return (cx, cy - 0.48), (cx, cy + 0.48)
    return (cx, cy + 0.48), (cx, cy - 0.48)


TARGETS = [(78.10, 17.50), (77.70, 17.35)]
for (cx, cy, rot) in [(81.5, 21.0, 180), (82.0, 20.0, 180),
                      (81.0, 22.0, 0), (82.5, 22.5, 180),
                      (80.5, 19.5, 270), (83.0, 20.5, 180)]:
    p1, p2 = pads(cx, cy, rot)
    hops = []
    for t in TARGETS:
        g, w = gate_track(0, 'PHY_1V8', p1[0], p1[1], t[0], t[1])
        hops.append((round(g, 3), t, w))
    best = (-9.9, None, None)
    for i in range(-6, 7):
        for j in range(-6, 7):
            if abs(i) + abs(j) == 0:
                continue
            vx, vy = p2[0] + i * 0.2, p2[1] + j * 0.2
            gv, _ = gate_via(vx, vy, 'GND')
            if gv > best[0]:
                gs, _ = gate_track(0, 'GND', p2[0], p2[1], vx, vy)
                best = (min(gv, gs), (round(vx, 2), round(vy, 2)),
                        (round(gv, 3), round(gs, 3)))
    print(f'site ({cx},{cy}) rot {rot}: pad1 ({p1[0]:.2f},{p1[1]:.2f}) '
          f'F hops {hops}; pad2 GND via at {best[1]} gate {best[0]:+.3f} '
          f'(via/stub {best[2]})')
print('=== done ===')
