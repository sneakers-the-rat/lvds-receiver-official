"""t_ax13: F-layer passability for +3V3D hw0.30 in the M3 box with
the SCL window via present. '#' passable '.' blocked."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import numpy as np

pool = load_board_pool()
W = (67.5, 5.8)
via = ('via', 'I2C_SCL', (W[0], W[1], 0.25), 0.2)
add_items({0: [via], 2: [via]})
pool[1].append(via)

sys.path.insert(0, 'hw')
from router import netclass
X0, X1, Y0, Y1, step = 66.6, 69.4, 5.4, 7.4, 0.1
xs = np.arange(X0, X1 + 1e-9, step)
ys = np.arange(Y0, Y1 + 1e-9, step)
GX, GY = np.meshgrid(xs, ys)


def df(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = GX - cx, GY - cy
        c, s = np.cos(-rot), np.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = GX - x1, GY - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    return np.hypot(GX - d[0], GY - d[1]) - d[2]


myclr = netclass('+3V3D')[1]
f = np.full(GX.shape, 9.9)
for it in pool[0]:
    if it[1] == '+3V3D':
        continue
    req = max(myclr, it[3])
    f = np.minimum(f, df(it) - req)
track = f >= 0.30
marks = {(67.375, 6.625): 'S', (68.625, 6.125): 'G', W: 'W'}
for iy in range(len(ys) - 1, -1, -1):
    row = ''
    for ix in range(len(xs)):
        x, y = xs[ix], ys[iy]
        ch = None
        for (mx, my), mc in marks.items():
            if abs(x - mx) < 0.06 and abs(y - my) < 0.06:
                ch = mc
        row += ch if ch else ('#' if track[iy, ix] else '.')
    print(f'y={ys[iy]:4.1f} {row}', flush=True)
print('x from 66.6 step 0.1', flush=True)
