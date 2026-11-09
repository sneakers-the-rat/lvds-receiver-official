"""t_ax8: render In2 passability for GND hw0.125 in the M1 box,
with the SCL via + approach seg present (as in t_ax6). '#' passable,
'.' blocked; mark S=start (66.375,6.125), G=goal via (67.375,4.125),
W=window via, T=THR_DAC via."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import numpy as np

pool = load_board_pool()
W = (67.4, 5.65)
seg = ('seg', 'I2C_SCL', (66.875, 6.75, W[0], W[1], 0.10), 0.2)
via = ('via', 'I2C_SCL', (W[0], W[1], 0.25), 0.2)
add_items({1: [seg], 0: [via], 1: [via], 2: [via]})

sys.path.insert(0, 'hw')
from router import netclass
print('netclass GND:', netclass('GND'), ' SCL:', netclass('I2C_SCL'),
      flush=True)

X0, X1, Y0, Y1, step = 65.4, 68.2, 3.4, 7.0, 0.1
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


myclr = netclass('GND')[1]
f = np.full(GX.shape, 9.9)
binder = {}
for it in pool[1]:
    if it[1] == 'GND':
        continue
    req = max(myclr, it[3])
    v = df(it) - req
    upd = v < f
    f = np.where(upd, v, f)
track = f >= 0.125
marks = {(66.375, 6.125): 'S', (67.375, 4.125): 'G', W: 'W',
         (66.625, 4.875): 'T', (66.2, 6.5): 'g'}
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
print('x from 65.4 step 0.1; start passable:',
      track[int(round((6.125 - Y0) / step)), int(round((66.375 - X0) / step))],
      'goal passable:',
      track[int(round((4.125 - Y0) / step)), int(round((67.375 - X0) / step))],
      flush=True)

# binder at specific cells (recompute df per item at a point)
for (px, py) in ((66.0, 5.4), (66.5, 5.4), (67.0, 5.45), (66.8, 5.5),
                 (66.6, 5.2), (67.2, 5.3)):
    best = []
    for it in pool[1]:
        if it[1] == 'GND':
            continue
        gx = np.array([[px]])
        gy = np.array([[py]])
        kind, d = it[0], it[2]
        if kind == 'pad':
            cx, cy, hw, hh, rot = d
            dx, dy = gx - cx, gy - cy
            c, s = np.cos(-rot), np.sin(-rot)
            lx, ly = dx * c - dy * s, dx * s + dy * c
            v = float(np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                               np.maximum(np.abs(ly) - hh, 0.0)))
        elif kind == 'seg':
            x1, y1, x2, y2, hw = d
            vx, vy = px - x1, py - y1
            dx, dy = x2 - x1, y2 - y1
            L2 = dx * dx + dy * dy
            t = 0.0 if L2 == 0 else max(0.0, min(1.0,
                                                 (vx * dx + vy * dy) / L2))
            v = float(np.hypot(vx - t * dx, vy - t * dy) - hw)
        else:
            v = float(np.hypot(px - d[0], py - d[1]) - d[2])
        best.append((v - max(myclr, it[3]), it))
    best.sort(key=lambda t: t[0])
    m, it = best[0]
    print(f'cell ({px},{py}): field {m:+.3f} binder {L.fmt_it(it)}',
          flush=True)
