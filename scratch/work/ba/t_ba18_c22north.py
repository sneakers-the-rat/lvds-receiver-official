"""t_ba18: gate C22 north-family candidate sites on exp252's
pool. 0402 pads at centre +-0.48 (x for rot 0/180, y for
90/270). For each site: pad1 PHY hop = 1-2 F segs to the PHY
via point (77.90,10.08); pad2 GND tie = best via site on a
0.2 grid within 1.3 mm (viafit vs ALL layers, KiCad numbers
r0.25/clr0.2 in the model classes) + F stub gate."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp252.kicad_pcb')
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
VIA_PT = (77.90, 10.08)


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
    it = ('via', net, (x, y, 0.25), 0.25 if net == 'PHY_1V8' else 0.2)
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


SITES = [(77.35, 9.35, 180), (76.85, 9.60, 180), (77.60, 8.90, 180),
         (76.50, 9.90, 180), (77.35, 9.35, 0), (77.10, 9.00, 180),
         (76.90, 9.20, 90), (77.50, 9.70, 270)]
for (cx, cy, rot) in SITES:
    p1, p2 = pads(cx, cy, rot)
    # pad1 hop: direct, or dogleg via midpoint pushed north
    g_direct, w_direct = gate_track(0, 'PHY_1V8', p1[0], p1[1],
                                    VIA_PT[0], VIA_PT[1])
    mx, my = (p1[0] + VIA_PT[0]) / 2, max(p1[1], VIA_PT[1]) + 0.15
    g_a, _ = gate_track(0, 'PHY_1V8', p1[0], p1[1], mx, my)
    g_b, _ = gate_track(0, 'PHY_1V8', mx, my, VIA_PT[0], VIA_PT[1])
    hop = max(g_direct, min(g_a, g_b))
    hopkind = 'direct' if g_direct >= min(g_a, g_b) else 'dogleg'
    # pad2 GND via search
    best = (-9.9, None, None)
    for i in range(-6, 7):
        for j in range(-6, 7):
            vx, vy = p2[0] + i * 0.2, p2[1] + j * 0.2
            if abs(i) + abs(j) == 0:
                continue
            gv, _ = gate_via(vx, vy, 'GND')
            if gv > best[0]:
                gs, _ = gate_track(0, 'GND', p2[0], p2[1], vx, vy)
                best = (min(gv, gs), (round(vx, 2), round(vy, 2)),
                        (round(gv, 3), round(gs, 3)))
    print(f'site ({cx},{cy}) rot {rot}: pad1 ({p1[0]:.2f},{p1[1]:.2f}) '
          f'hop {hop:+.3f} ({hopkind}, direct worst vs {w_direct}); '
          f'pad2 ({p2[0]:.2f},{p2[1]:.2f}) GND via at {best[1]} '
          f'gate {best[0]:+.3f} (via/stub {best[2]})')
print('=== done ===')
