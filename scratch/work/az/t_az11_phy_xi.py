"""t_az11: (1) print PHY's full journey under S4; (2) flood XI on the
S6 pool from U7.28 and report the strait fences.
"""
import sys, math
import numpy as np
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L
sys.path.insert(0, 'scratch/work/az')
from t_az10_astar_scen import apply_scen  # noqa

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'

pool = load_board_pool(BOARD)
apply_scen(pool, 'S4')
astar = make_astar((68.0, 82.0, 6.0, 22.0), 0.125)
r = astar('PHY_1V8', ((0,), 72.02, 18.0), (2, 77.8, 16.2), 0.10)
print('PHY S4 journey to B (77.8,16.2):')
print('  vias:', r['vias'])
for rn in r['runs']:
    pts = rn['pts']
    print(f"  L{rn['layer']} run {len(pts)} pts: {pts[0]} -> {pts[-1]}")
    # print points where x crosses 75.9..76.6
    cross = [p for p in pts if 75.9 <= p[0] <= 76.6]
    if cross:
        print('    crossing-band pts:', cross)

# ---- XI flood on S6 pool ----
pool = load_board_pool(BOARD)
apply_scen(pool, 'S6')
frags = fragments('XI', (64.0, 92.0, 0.0, 26.0))
print('XI fragments (S6):', len(frags))
start_i = None
for i, fr in enumerate(frags):
    for (l, it) in fr['items']:
        if it[0] == 'pad' and abs(it[2][0] - 76.25) < 0.01:
            start_i = i
print('  start fragment (U7.28):', start_i)

X0, X1, Y0, Y1, STEP = 64.0, 92.0, 0.0, 26.0, 0.125
xs = np.arange(X0, X1 + 1e-9, STEP)
ys = np.arange(Y0, Y1 + 1e-9, STEP)
GX, GY = np.meshgrid(xs, ys)
NX, NY = len(xs), len(ys)


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


NET = 'XI'
myclr = 0.2
fields = {}
for l in range(3):
    f = np.full(GX.shape, 9.9)
    for it in pool[l]:
        a = bb(it)
        if a[1] < X0 - 1 or a[0] > X1 + 1 or a[3] < Y0 - 1 or a[2] > Y1 + 1:
            continue
        if it[1] == NET:
            continue
        f = np.minimum(f, df_grid(it) - max(myclr, it[3]))
    fields[l] = f
track = {l: fields[l] >= 0.10 for l in range(3)}
viafit = (np.minimum(np.minimum(fields[0], fields[1]), fields[2]) >= 0.25)
ownd = {l: np.full(GX.shape, 9.9) for l in range(3)}
for (l, it) in frags[start_i]['items']:
    ownd[l] = np.minimum(ownd[l], df_grid(it))
from collections import deque
seen = {l: np.zeros(GX.shape, dtype=bool) for l in range(3)}
dq = deque()
for l in {l for (l, _) in frags[start_i]['items']}:
    cells = np.argwhere((ownd[l] <= 0.13) & track[l])
    for iy, ix in cells:
        if not seen[l][iy, ix]:
            seen[l][iy, ix] = True
            dq.append((l, iy, ix))
while dq:
    l, iy, ix = dq.popleft()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            jy, jx = iy + dy, ix + dx
            if 0 <= jy < NY and 0 <= jx < NX and not seen[l][jy, jx] \
                    and track[l][jy, jx]:
                seen[l][jy, jx] = True
                dq.append((l, jy, jx))
    if viafit[iy, ix]:
        for l2 in range(3):
            if l2 != l and not seen[l2][iy, ix] and track[l2][iy, ix]:
                seen[l2][iy, ix] = True
                dq.append((l2, iy, ix))
for l in range(3):
    ys_r, xs_r = np.where(seen[l])
    if len(ys_r):
        print(f'  reached L{l}: x[{xs[xs_r].min():.2f},{xs[xs_r].max():.2f}] '
              f'y[{ys[ys_r].min():.2f},{ys[ys_r].max():.2f}] cells={len(ys_r)}')
# target points of the arc fragment
for i, fr in enumerate(frags):
    if i == start_i:
        continue
    pts = []
    for (l, it) in fr['items']:
        if it[0] == 'via':
            pts.append((l, it[2][0], it[2][1]))
        elif it[0] == 'pad':
            pts.append((l, it[2][0], it[2][1]))
    best = None
    for (l, px, py) in pts:
        iy0, ix0 = int(round((py - Y0) / STEP)), int(round((px - X0) / STEP))
        for jy in range(NY):
            pass
        # nearest seen cell on same layer
        ys_r, xs_r = np.where(seen[l])
        if len(ys_r):
            d = np.hypot(xs[xs_r] - px, ys[ys_r] - py)
            k = np.argmin(d)
            if best is None or d[k] < best[0]:
                best = (float(d[k]), (l, px, py),
                        (float(xs[xs_r][k]), float(ys[ys_r][k])))
    print(f'  frag{i}: nearest approach {best}')
print('=== done ===')
