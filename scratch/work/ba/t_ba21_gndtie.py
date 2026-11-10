"""t_ba21: diagnose the GND tie for C22 at (77.5,9.7) rot 270
(pad2 at (77.5,9.22)). Scan GND via candidates over
x[76.0,78.8] y[8.0,10.6] step 0.2 printing gate + worst
offender for the best 8; gate the F GND track from pad2 to
the two best via candidates."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp252.kicad_pcb')
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
P2 = (77.5, 9.22)


def _near(l, x, y, r):
    return [o for o in pool[l]
            if abs(C(o)[0] - x) < r and abs(C(o)[1] - y) < r]


def gate_via_full(x, y, net='GND'):
    it = ('via', net, (x, y, 0.25), 0.2)
    worst, wo = 9.9, None
    for l in range(3):
        for o in _near(l, x, y, 3.0):
            if o[1] == net:
                continue
            m = item_margin(l, it, [o])
            if m < worst:
                worst, wo = m, (LAYN[l], o[1], o[0],
                                (round(C(o)[0], 2), round(C(o)[1], 2)))
    return worst, wo


def gate_track(l, net, x1, y1, x2, y2, hw=0.10):
    it = ('seg', net, (x1, y1, x2, y2, hw), 0.2)
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


cands = []
for i in range(15):
    for j in range(14):
        vx, vy = 76.0 + i * 0.2, 8.0 + j * 0.2
        g, wo = gate_via_full(vx, vy)
        cands.append((round(g, 3), (round(vx, 2), round(vy, 2)), wo))
cands.sort(reverse=True)
print('best GND via candidates:')
for c in cands[:8]:
    print('  ', c)
for c in cands[:3]:
    vx, vy = c[1]
    g1, w1 = gate_track(0, 'GND', P2[0], P2[1], vx, vy)
    print(f'GND track pad2->({vx},{vy}): {g1:+.3f} vs {w1}')
# dogleg west then south
for (mx, my, vx, vy) in [(77.0, 9.15, 76.42, 9.0), (76.9, 9.3, 76.42, 9.0)]:
    g1, w1 = gate_track(0, 'GND', P2[0], P2[1], mx, my)
    g2, w2 = gate_track(0, 'GND', mx, my, vx, vy)
    gv, wo = gate_via_full(vx, vy)
    print(f'dogleg via ({mx},{my}) to ({vx},{vy}): legs {g1:+.3f}/{g2:+.3f}'
          f' via {gv:+.3f} worst {wo}')
print('=== done ===')
