"""t_ax17: replay via+M1+M2+M3 (as t_ax11), then render B-layer
passability for I2C_SCL hw0.10 in (66,71,-0.5,7) and dump M2's new
LOL segs + M4-relevant B items."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import numpy as np

W = (67.5, 5.8)
pool = load_board_pool()
via = ('via', 'I2C_SCL', (W[0], W[1], 0.25), 0.2)
seg = ('seg', 'I2C_SCL', (66.875, 6.75, W[0], W[1], 0.10), 0.2)
add_items({0: [via], 2: [via]})
pool[1].append(via)
pool[1].append(seg)

rip = chain_segs(pool, 'GND', 1, (66.375, 6.125), (67.375, 4.125))
rip_items(rip)
astar = make_astar((65.4, 68.2, 3.4, 7.0), 0.025)
J = astar('GND', ((1,), 66.375, 6.125), (1, 67.375, 4.125), hw=0.125)
add_items(journey_items_dense(J, 'GND', hw=0.125))

rip = chain_segs(pool, 'CDR_LOL', 2, (67.625, 6.625), (68.375, 4.125))
rip_items(rip)
astar = make_astar((66.2, 70.6, 3.0, 8.0), 0.025)
J = astar('CDR_LOL', ((2,), 67.625, 6.625), (2, 68.375, 4.125),
          hw=0.125, layer_lock=[0, 0, 1])
its = journey_items_dense(J, 'CDR_LOL', hw=0.125)
add_items(its)
print('M2 new LOL B segs:', flush=True)
for it in its[2]:
    print('  ', L.fmt_it(it), flush=True)

sys.path.insert(0, 'hw')
from router import netclass
X0, X1, Y0, Y1, step = 65.5, 72.5, -2.6, 3.2, 0.125
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


myclr = netclass('I2C_SCL')[1]
f = np.full(GX.shape, 9.9)
for it in pool[2]:
    if it[1] == 'I2C_SCL':
        continue
    req = max(myclr, it[3])
    f = np.minimum(f, df(it) - req)
track = f >= 0.10
marks = {W: 'W', (69.35, 1.4): 'P'}
for iy in range(len(ys) - 1, -1, -1):
    row = ''
    for ix in range(len(xs)):
        x, y = xs[ix], ys[iy]
        ch = None
        for (mx, my), mc in marks.items():
            if abs(x - mx) < 0.07 and abs(y - my) < 0.07:
                ch = mc
        row += ch if ch else ('#' if track[iy, ix] else '.')
    print(f'y={ys[iy]:5.2f} {row}', flush=True)
print('x from 66.0 step 0.125', flush=True)
