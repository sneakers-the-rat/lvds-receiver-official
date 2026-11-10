"""t_az3: ASCII passability maps for the quadrant, per target net.
For each net, per layer: '.' = a w0.2 track centre fits (exact distance
field >= 0.10), 'V' = also via-fit (all-layer field >= 0.25),
'#' = blocked. Same-net items are passable ('o' marks same-net copper
cells). Box x[70,84], y[8,23], step 0.25. Uses the t_ax0_pre pool
(faithful exp251 load) and the au71 field construction."""
import sys, math
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
import numpy as np
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')

X0, X1, Y0, Y1, STEP = 70.0, 84.0, 8.0, 23.0, 0.25
xs = np.arange(X0, X1 + 1e-9, STEP)
ys = np.arange(Y0, Y1 + 1e-9, STEP)
GX, GY = np.meshgrid(xs, ys)

def df(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = GX - cx, GY - cy
        c, s = math.cos(-rot), math.sin(-rot)
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

def bb(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        r = math.hypot(d[2], d[3])
        return d[0] - r, d[0] + r, d[1] - r, d[1] + r
    if kind == 'seg':
        return (min(d[0], d[2]) - d[4], max(d[0], d[2]) + d[4],
                min(d[1], d[3]) - d[4], max(d[1], d[3]) + d[4])
    return d[0] - d[2], d[0] + d[2], d[1] - d[2], d[1] + d[2]

from router import netclass

for net in ('XI', 'PHY_1V8', 'USB_RST'):
    myclr = netclass(net)[1]
    G = {}
    own = {}
    for l in range(3):
        f = np.full(GX.shape, 9.9)
        o = np.zeros(GX.shape, dtype=bool)
        for it in pool[l]:
            a, b, c2, d2 = bb(it)
            if b < X0 - 1 or a > X1 + 1 or d2 < Y0 - 1 or c2 > Y1 + 1:
                continue
            if it[1] == net:
                o |= df(it) <= 0.05
                continue
            req = max(myclr, it[3])
            f = np.minimum(f, df(it) - req)
        G[l] = f
        own[l] = o
    viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
    print(f'##### {net} (clr {myclr}) #####')
    hdr = '      ' + ''.join(str(int(x) % 10) if abs(x - round(x)) < 1e-9
                             else ' ' for x in xs)
    for l, ln in ((0, 'F'), (1, 'In2'), (2, 'B')):
        print(f'--- layer {ln} ---')
        print(hdr)
        for iy in range(len(ys) - 1, -1, -1):
            row = ''
            for ix in range(len(xs)):
                if own[l][iy, ix]:
                    row += 'o'
                elif viafit[iy, ix] and G[l][iy, ix] >= 0.10:
                    row += 'V'
                elif G[l][iy, ix] >= 0.10:
                    row += '.'
                else:
                    row += '#'
            print(f'y={ys[iy]:5.2f} {row}')
    sys.stdout.flush()
