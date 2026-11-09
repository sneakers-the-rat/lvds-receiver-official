"""t_aw34: G-field forensics for the SCL bridge. Rebuild the A*
field for I2C_SCL over the bridge box (replicated from au71's
make_astar), print G at start/goal cells, BFS the per-layer track
reachability from the start cell, and scan viafit in the corridor."""
import wx
_app = wx.App(False)
import sys, json, pickle, math
sys.path.insert(0, 'scratch/work/au')
import numpy as np
g = {'__name__': 'aw34'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
st = pickle.load(open('scratch/work/aw/state_aw.pkl', 'rb'))
_ns = {id(g): g}
for _fn in (g['fragments'], g['item_margin'], g['make_astar'],
            g['try_emit'], g['journey_items_dense']):
    _ns[id(_fn.__globals__)] = _fn.__globals__
for _d in _ns.values():
    _d['pool'] = st['pool']
    _d['NEW'] = st['NEW']
    _d['JOURNEYS'] = st['JOURNEYS']
    _d['NET_HW'] = st['NET_HW']
pool = st['pool']
from router import netclass

X0, X1, Y0, Y1 = 63.0, 71.5, -1.0, 8.5
step = 0.025
xs = np.arange(X0, X1 + 1e-9, step)
ys = np.arange(Y0, Y1 + 1e-9, step)
GXm, GYm = np.meshgrid(xs, ys)


def df(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = GXm - cx, GYm - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = GXm - x1, GYm - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    return np.hypot(GXm - d[0], GYm - d[1]) - d[2]


def bb(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        r = math.hypot(d[2], d[3])
        return d[0] - r, d[0] + r, d[1] - r, d[1] + r
    if kind == 'seg':
        return (min(d[0], d[2]) - d[4], max(d[0], d[2]) + d[4],
                min(d[1], d[3]) - d[4], max(d[1], d[3]) + d[4])
    return d[0] - d[2], d[0] + d[2], d[1] - d[2], d[1] + d[2]


net = 'I2C_SCL'
myclr = netclass(net)[1]
G = {}
for l in range(3):
    f = np.full(GXm.shape, 9.9)
    for it in pool[l]:
        if it[1] == net:
            continue
        a, b, c2, d2 = bb(it)
        req = max(myclr, it[3])
        if b < X0 - req - 0.3 or a > X1 + req + 0.3 or \
           d2 < Y0 - req - 0.3 or c2 > Y1 + req + 0.3:
            continue
        f = np.minimum(f, df(it) - req)
    G[l] = f


def cell(x, y):
    return (int(round((y - Y0) / step)), int(round((x - X0) / step)))


for (label, (px, py)) in {'start (66.875,6.75)': (66.875, 6.75),
                          'goal (69.35,1.4)': (69.35, 1.4)}.items():
    iy, ix = cell(px, py)
    print(f'{label}: G = {[round(float(G[l][iy, ix]), 3) for l in range(3)]}',
          flush=True)

hw = 0.1
track = {l: G[l] >= hw for l in range(3)}
viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25

from collections import deque
for l in range(3):
    sc = cell(66.875, 6.75)
    seen = np.zeros(track[l].shape, dtype=bool)
    if track[l][sc]:
        dq = deque([sc])
        seen[sc] = True
        while dq:
            (iy, ix) = dq.popleft()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    jy, jx = iy + dy, ix + dx
                    if 0 <= jy < seen.shape[0] and 0 <= jx < seen.shape[1] \
                            and not seen[jy, jx] and track[l][jy, jx]:
                        seen[jy, jx] = True
                        dq.append((jy, jx))
    tc = cell(69.35, 1.4)
    # E-most / S-most reach in the box's SE quadrant
    ys_r, xs_r = np.where(seen)
    print(f'L{l}: start-cell reachable cells={int(seen.sum())} '
          f'goal-cell track={bool(track[l][tc])} '
          f'goal reached={bool(seen[tc]) if track[l][sc] else False}',
          flush=True)
    if len(xs_r):
        # max x reached at y in [1.0,2.0]
        band = [(float(xs[j]), float(ys[i])) for (i, j) in zip(ys_r, xs_r)
                if 1.0 <= float(ys[i]) <= 2.0]
        if band:
            print(f'   E-most reach at y1-2: x={max(b[0] for b in band):.2f}',
                  flush=True)

# viafit cells in the corridor between the diagonals: y 3..6, x 64..70
iy0, ix0 = cell(64.0, 3.0)
iy1, ix1 = cell(70.0, 6.0)
sub = viafit[iy0:iy1, ix0:ix1]
print(f'viafit cells in corridor (64-70, 3-6): {int(sub.sum())}',
      flush=True)
# viafit anywhere in box
print(f'viafit cells total in box: {int(viafit.sum())}', flush=True)
# where are viafit cells? sample columns
for xx in (64.0, 65.0, 66.0, 67.0, 68.0, 69.0, 70.0):
    _, ix = cell(xx, 0)
    col = np.where(viafit[:, ix])[0]
    if len(col):
        print(f'  viafit at x={xx}: y from {float(ys[col.min()]):.2f} '
              f'to {float(ys[col.max()]):.2f} (n={len(col)})', flush=True)
    else:
        print(f'  viafit at x={xx}: NONE', flush=True)
print('T_AW34 COMPLETE', flush=True)

print('--- corridor probes ---', flush=True)
def grow(l, pts):
    out = []
    for (px, py) in pts:
        iy, ix = cell(px, py)
        out.append(f'({px},{py}):{float(G[l][iy, ix]):+.2f}')
    return ' '.join(out)
print('F col x65.2 y6.75->1.75:', grow(0, [(65.2, y) for y in (6.75, 6.0, 5.0, 4.0, 3.0, 2.5, 2.0, 1.75)]), flush=True)
print('B col x65.2 y6.75->1.75:', grow(2, [(65.2, y) for y in (6.75, 6.0, 5.0, 4.0, 3.0, 2.5, 2.0, 1.75)]), flush=True)
print('F row y1.63 x65.2->66.5:', grow(0, [(x, 1.63) for x in (65.2, 65.6, 66.0, 66.3, 66.5)]), flush=True)
print('In2 col x65.2 y6.75->6.0:', grow(1, [(65.2, y) for y in (6.75, 6.5, 6.0)]), flush=True)
print('B row y-0.5 x65->69.35:', grow(2, [(x, -0.5) for x in (65.0, 66.0, 67.0, 68.0, 69.0, 69.35)]), flush=True)
print('B col x69.35 y-0.5->1.4:', grow(2, [(69.35, y) for y in (-0.5, 0.0, 0.5, 1.0, 1.4)]), flush=True)
print('F col x66.3 y3->1.63:', grow(0, [(66.3, y) for y in (3.0, 2.5, 2.0, 1.63)]), flush=True)
print('In2 row y6.75 x66.875->65.2:', grow(1, [(x, 6.75) for x in (66.875, 66.4, 66.0, 65.6, 65.2)]), flush=True)
