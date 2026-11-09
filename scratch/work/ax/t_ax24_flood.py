"""t_ax24: reachability flood for I2C_SCL from the stub via
(69.625,12.625) on the A*'s own fields (track = G>=hw per layer,
viafit = min G >= 0.25), box (68.5,76.5,3,13.5) step 0.05.
Prints per-layer reachable maps ('#' reached, '.' passable unreached,
' ' impassable) and whether the B diagonal / pocket via are reached."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import numpy as np
from collections import deque

pool = load_board_pool()
sys.path.insert(0, 'hw')
from router import netclass
X0, X1, Y0, Y1, step = 68.5, 76.5, 3.0, 13.5, 0.05
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
G = {}
for l in range(3):
    f = np.full(GX.shape, 9.9)
    for it in pool[l]:
        if it[1] == 'I2C_SCL':
            continue
        req = max(myclr, it[3])
        f = np.minimum(f, df(it) - req)
    G[l] = f
track = {l: G[l] >= 0.10 for l in range(3)}
viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
NY, NX = GX.shape


def cell(x, y):
    return (int(round((y - Y0) / step)), int(round((x - X0) / step)))


seen = {l: np.zeros((NY, NX), dtype=bool) for l in range(3)}
dq = deque()
sy, sx = cell(69.625, 12.625)
for l in range(3):
    if track[l][sy, sx]:
        seen[l][sy, sx] = True
        dq.append((l, sy, sx))
while dq:
    l, iy, ix = dq.popleft()
    for l2 in range(3):
        if l2 != l and viafit[iy, ix] and track[l2][iy, ix] \
                and not seen[l2][iy, ix]:
            seen[l2][iy, ix] = True
            dq.append((l2, iy, ix))
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            jy, jx = iy + dy, ix + dx
            if 0 <= jy < NY and 0 <= jx < NX and track[l][jy, jx] \
                    and not seen[l][jy, jx]:
                seen[l][jy, jx] = True
                dq.append((l, jy, jx))
for l, nm in ((0, 'F'), (1, 'In2'), (2, 'B')):
    gy, gx = cell(69.35, 1.4)
    print(f'layer {nm}: cells reached {seen[l].sum()}', flush=True)
# print B layer map (coarse 0.25 sampling)
for iy in range(NY - 1, -1, -4):
    row = ''
    for ix in range(0, NX, 4):
        if seen[2][iy, ix]:
            row += '#'
        elif track[2][iy, ix]:
            row += '.'
        else:
            row += ' '
    print(f'y={ys[iy]:5.2f} {row}', flush=True)
print('x from 68.5 step 0.2 (every 4th col of 0.05 grid)', flush=True)
