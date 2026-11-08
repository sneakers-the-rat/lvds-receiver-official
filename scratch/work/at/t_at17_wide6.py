"""t_at17: widest-path diagnosis on the v6 model (pool from t_at16)."""
import wx
_app = wx.App(False)
import sys, math, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

src = open('scratch/work/at/t_at16_astar6.py').read()
exec(src.split('X0, X1, Y0, Y1, ST')[0].split('def gate_news')[0])

X0, X1, Y0, Y1, ST = 63.0, 79.5, -3.0, 29.5, 0.05
xs = np.arange(X0, X1 + 1e-9, ST)
ys = np.arange(Y0, Y1 + 1e-9, ST)
GX, GY = np.meshgrid(xs, ys)
NY, NX = GX.shape

def item_dist_field(it):
    kind, dd = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = dd
        dx, dy = GX - cx, GY - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = dd
        px, py = GX - x1, GY - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    cx, cy, r = dd
    return np.hypot(GX - cx, GY - cy) - r

def item_bbox(it):
    kind, dd = it[0], it[2]
    if kind == 'pad':
        r = math.hypot(dd[2], dd[3])
        return dd[0] - r, dd[0] + r, dd[1] - r, dd[1] + r
    if kind == 'seg':
        return (min(dd[0], dd[2]) - dd[4], max(dd[0], dd[2]) + dd[4],
                min(dd[1], dd[3]) - dd[4], max(dd[1], dd[3]) + dd[4])
    return dd[0] - dd[2], dd[0] + dd[2], dd[1] - dd[2], dd[1] + dd[2]

def build_fields(net):
    myclr = netclass(net)[1]
    G, ARG = {}, {}
    for l in range(3):
        field = np.full(GX.shape, 9.9)
        arg = np.full(GX.shape, -1, dtype=int)
        for idx, it in enumerate(pool[l]):
            if it[1] == net:
                continue
            bx0, bx1, by0, by1 = item_bbox(it)
            req = max(myclr, it[3])
            if bx1 < X0 - req - 0.3 or bx0 > X1 + req + 0.3 or \
               by1 < Y0 - req - 0.3 or by0 > Y1 + req + 0.3:
                continue
            f = item_dist_field(it) - req
            m = f < field
            field = np.where(m, f, field)
            arg = np.where(m, idx, arg)
        G[l] = field
        ARG[l] = arg
    return G, ARG

def cell(x, y):
    return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))

CASES = {
    'CAP_CLK':  dict(start=(70.15, 1.72), target=(75.45, 25.385)),
    'CAP_DATA': dict(start=(69.90, 3.18), target=(75.45, 22.845)),
}

def widest(net):
    G, ARG = build_fields(net)
    case = CASES[net]
    viafit = np.minimum(np.minimum(G[0], G[1]), G[2])
    sc = cell(*case['start'])
    tc = cell(*case['target'])
    best = {}
    pq = [(-9.9, (1, sc[0], sc[1]))]
    best[(1, sc[0], sc[1])] = 9.9
    came = {}
    goal = None
    while pq:
        negb, p = heapq.heappop(pq)
        b = -negb
        if b < best.get(p, -9.9) - 1e-12:
            continue
        l, iy, ix = p
        if l == 0 and (iy, ix) == tc:
            goal = p
            break
        for l2 in range(3):
            if l2 == l:
                continue
            nb = min(b, float(viafit[iy, ix]) - 0.25)
            q = (l2, iy, ix)
            if nb > best.get(q, -9.9) + 1e-12:
                best[q] = nb
                came[q] = p
                heapq.heappush(pq, (-nb, q))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                jy, jx = iy + dy, ix + dx
                if not (0 <= jy < NY and 0 <= jx < NX):
                    continue
                nb = min(b, float(G[l][jy, jx]) - 0.10)
                q = (l, jy, jx)
                if nb > best.get(q, -9.9) + 1e-12:
                    best[q] = nb
                    came[q] = p
                    heapq.heappush(pq, (-nb, q))
    if goal is None:
        return None, []
    bval = best[goal]
    p = goal
    chain = [p]
    while p in came:
        p = came[p]
        chain.append(p)
    chain.reverse()
    binds = []
    for i, p in enumerate(chain):
        l, iy, ix = p
        v = float(G[l][iy, ix]) - 0.10
        if v <= bval + 0.01:
            ai = ARG[l][iy, ix]
            binds.append((l, round(float(xs[ix]), 2),
                          round(float(ys[iy]), 2), round(v, 3),
                          L.fmt_it(pool[l][ai]) if ai >= 0 else None))
        if i + 1 < len(chain) and chain[i + 1][0] != l:
            vv = float(viafit[iy, ix]) - 0.25
            if vv <= bval + 0.01:
                ai = ARG[l][iy, ix]
                binds.append((l, round(float(xs[ix]), 2),
                              round(float(ys[iy]), 2), round(vv, 3),
                              'VIAFIT ' + (L.fmt_it(pool[l][ai])
                                           if ai >= 0 else '?')))
    return bval, binds

for net in ('CAP_CLK', 'CAP_DATA'):
    b, binds = widest(net)
    print(f'== {net}: widest bottleneck = '
          f'{("None" if b is None else format(b, "+.3f"))}', flush=True)
    seen = set()
    n = 0
    for bd in binds:
        if bd[4] in seen:
            continue
        seen.add(bd[4])
        n += 1
        if n > 14:
            break
        print(f'   bind L{bd[0]} ({bd[1]},{bd[2]}) {bd[3]:+.3f} '
              f'vs {bd[4]}', flush=True)
