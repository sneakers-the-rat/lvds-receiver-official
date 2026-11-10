"""t_az9: exact viafit scanner for the XI pocket under fence-move
scenarios. viafit margin at (x,y) = min over layers of
(foreign-field - 0.25), foreign = all nets except XI. Feasible: >= 0.
Scenarios are model-level re-lays applied with rip_items/add_items.
"""
import sys, math
import numpy as np
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'
X0, X1, Y0, Y1, STEP = 75.85, 76.70, 9.90, 11.20, 0.025
xs = np.arange(X0, X1 + 1e-9, STEP)
ys = np.arange(Y0, Y1 + 1e-9, STEP)
GX, GY = np.meshgrid(xs, ys)


def bb(it):
    if it[0] == 'pad':
        cx, cy, hw, hh, rot = it[2]
        if rot:
            c, s = abs(math.cos(rot)), abs(math.sin(rot))
            ex, ey = hw * c + hh * s, hw * s + hh * c
        else:
            ex, ey = hw, hh
        return (cx - ex, cx + ex, cy - ey, cy + ey)
    if it[0] == 'via':
        return (it[2][0] - it[2][2], it[2][0] + it[2][2],
                it[2][1] - it[2][2], it[2][1] + it[2][2])
    x1, y1, x2, y2, hw = it[2]
    return (min(x1, x2) - hw, max(x1, x2) + hw,
            min(y1, y2) - hw, max(y1, y2) + hw)


def df_grid(it):
    if it[0] == 'pad':
        cx, cy, hw, hh, rot = it[2]
        dx = np.maximum(np.abs(GX - cx) - hw, 0.0)
        dy = np.maximum(np.abs(GY - cy) - hh, 0.0)
        return np.hypot(dx, dy)
    if it[0] == 'via':
        return np.hypot(GX - it[2][0], GY - it[2][1]) - it[2][2]
    x1, y1, x2, y2, hw = it[2]
    vx, vy = x2 - x1, y2 - y1
    L2 = vx * vx + vy * vy
    if L2 == 0:
        return np.hypot(GX - x1, GY - y1) - hw
    t = np.clip(((GX - x1) * vx + (GY - y1) * vy) / L2, 0.0, 1.0)
    return np.hypot(GX - (x1 + t * vx), GY - (y1 + t * vy)) - hw


def scan(pool, label):
    marg = np.full(GX.shape, 9.9)
    for l in range(3):
        f = np.full(GX.shape, 9.9)
        for it in pool[l]:
            a = bb(it)
            if a[1] < X0 - 1 or a[0] > X1 + 1 or a[3] < Y0 - 1 or a[2] > Y1 + 1:
                continue
            if it[1] == 'XI':
                continue
            f = np.minimum(f, df_grid(it) - it[3])
        marg = np.minimum(marg, f - 0.25)
    feas = marg >= 0.0
    n = int(feas.sum())
    best = np.unravel_index(np.argmax(marg), marg.shape)
    print(f'{label}: feasible cells={n} best margin '
          f'{marg[best]:+.3f} at ({xs[best[1]]:.3f},{ys[best[0]]:.3f})')
    if n:
        pts = [(round(float(xs[j]), 3), round(float(ys[i]), 3),
                round(float(marg[i, j]), 3))
               for i, j in zip(*np.where(feas))]
        pts.sort(key=lambda t: -t[2])
        print('   top feasible:', pts[:12])
    return marg


def seg(net, x1, y1, x2, y2, hw=0.10, clr=0.2):
    return ('seg', net, (x1, y1, x2, y2, hw), clr)


def via(net, x, y, r=0.25, clr=0.2):
    return ('via', net, (x, y, r), clr)


def add(pool, l, its):
    add_items({l: its})


def scenario(pool, name):
    if name == 'S0':
        return
    if name in ('S1', 'S2', 'S3', 'S4'):
        # M-notch: notch via (75.737,10.75) -> (75.65,10.60)
        rip_items([it for l in range(3) for it in pool[l]
                   if it[1] == 'PHY_1V8A' and it[0] == 'via'
                   and abs(it[2][0] - 75.737) < 0.01
                   and abs(it[2][1] - 10.75) < 0.01])
        rip_items([it for it in pool[0]
                   if it[1] == 'PHY_1V8A' and it[0] == 'seg'
                   and C(it)[0] > 75.6 and C(it)[1] > 10.6])
        rip_items([it for it in pool[2]
                   if it[1] == 'PHY_1V8A' and it[0] == 'seg'
                   and abs(it[2][0] - 75.737) < 0.01
                   and abs(it[2][1] - 10.75) < 0.01])
        add(pool, 0, [via('PHY_1V8A', 75.65, 10.60, 0.25, 0.25),
                      seg('PHY_1V8A', 75.75, 11.562, 75.65, 10.60, 0.10, 0.25)])
        add(pool, 1, [via('PHY_1V8A', 75.65, 10.60, 0.25, 0.25)])
        add(pool, 2, [via('PHY_1V8A', 75.65, 10.60, 0.25, 0.25),
                      seg('PHY_1V8A', 75.65, 10.60, 75.30, 11.35, 0.10, 0.25)])
    if name in ('S2', 'S3', 'S4'):
        # M-xo: XO F escape re-lay (stub -> y10.9 run -> diag to (75.25,9.6))
        rip_items([it for it in pool[0]
                   if it[1] == 'XO' and it[0] == 'seg'
                   and 76.2 < C(it)[0] < 77.0 and 10.3 < C(it)[1] < 11.7])
        rip_items([it for it in pool[0]
                   if it[1] == 'XO' and it[0] == 'seg'
                   and 75.8 < C(it)[0] < 76.6 and 10.3 < C(it)[1] < 11.0])
        add(pool, 0, [seg('XO', 76.75, 11.562, 76.725, 10.90),
                      seg('XO', 76.725, 10.90, 76.00, 10.90),
                      seg('XO', 76.00, 10.90, 75.25, 9.60)])
    if name in ('S3', 'S4'):
        # M-s1: +3V3A In2 S1 re-laid east, rejoining node (76.625,10.25)
        rip_items([it for it in pool[1]
                   if it[1] == '+3V3A' and it[0] == 'seg'
                   and abs(it[2][0] - 77.125) < 0.01
                   and abs(it[2][1] - 13.125) < 0.01
                   and abs(it[2][2] - 76.625) < 0.01
                   and abs(it[2][3] - 10.25) < 0.01])
        add(pool, 1, [seg('+3V3A', 77.125, 13.125, 77.55, 11.60, 0.10, 0.25),
                      seg('+3V3A', 77.55, 11.60, 77.20, 10.50, 0.10, 0.25),
                      seg('+3V3A', 77.20, 10.50, 76.625, 10.25, 0.10, 0.25)])
    if name == 'S4':
        # + STP B staircase ripped in pocket band y[10,13.6] x[75.9,76.6]
        rip_items([it for it in pool[2]
                   if it[1] == 'ULPI_STP' and it[0] == 'seg'
                   and 75.9 < C(it)[0] < 76.6 and 10.0 < C(it)[1] < 13.6])


for name in ('S0', 'S1', 'S2', 'S3', 'S4'):
    pool = load_board_pool(BOARD)
    scenario(pool, name)
    scan(pool, name)
print('=== done ===')
