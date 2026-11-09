"""t_au25: 3-layer maximin for the SCL chord in the au24 model
(DATA entry placed, frag bowed). State (layer, cell); via transition
value = min over layers of field at the cell (track needs the cell's
own layer field; report bottleneck state + binder per layer."""
import wx
_app = wx.App(False)
import sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
src = open('scratch/work/au/t_au24_chain.py').read()
head = src.split('# ---- fine A* machinery')[0]
g = {'__name__': 'chaindata'}
exec(head, g)
pool = g['pool']
jd = json.load(open('scratch/work/au/entry_au24_DATA.json'))
items = g['journey_items_dense'](jd, 'CAP_DATA')
for l in range(3):
    pool[l] += items[l]

FX0, FX1, FY0, FY1, FST = 62.0, 72.0, -1.0, 9.0, 0.025
fxs = np.arange(FX0, FX1 + 1e-9, FST)
fys = np.arange(FY0, FY1 + 1e-9, FST)
FGX, FGY = np.meshgrid(fxs, fys)


def dist_field(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = FGX - cx, FGY - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = FGX - x1, FGY - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    cx, cy, r = d
    return np.hypot(FGX - cx, FGY - cy) - r


def bbox(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        r = math.hypot(d[2], d[3])
        return d[0] - r, d[0] + r, d[1] - r, d[1] + r
    if kind == 'seg':
        return (min(d[0], d[2]) - d[4], max(d[0], d[2]) + d[4],
                min(d[1], d[3]) - d[4], max(d[1], d[3]) + d[4])
    return d[0] - d[2], d[0] + d[2], d[1] - d[2], d[1] + d[2]


from router import netclass
F, ARG = {}, {}
for LAYER in range(3):
    myclr = netclass('I2C_SCL')[1]
    f = np.full(FGX.shape, 9.9)
    arg = np.full(FGX.shape, '', dtype=object)
    for it in pool[LAYER]:
        if it[1] == 'I2C_SCL':
            continue
        bx0, bx1, by0, by1 = bbox(it)
        req = max(myclr, it[3])
        if bx1 < FX0 - req - 0.3 or bx0 > FX1 + req + 0.3 or \
           by1 < FY0 - req - 0.3 or by0 > FY1 + req + 0.3:
            continue
        d = dist_field(it) - req
        m = d < f
        f = np.where(m, d, f)
        arg = np.where(m, f'{it[1]} {it[0]} {it[2]}', arg)
    F[LAYER], ARG[LAYER] = f, arg
VIAF = np.minimum(np.minimum(F[0], F[1]), F[2])

NY, NX = F[0].shape
sc = (int(round((1.40 - FY0) / FST)), int(round((69.35 - FX0) / FST)))
tc = (int(round((5.125 - FY0) / FST)), int(round((67.875 - FX0) / FST)))
best = {}
prev = {}
pq = []
for l in range(3):
    s0 = (l, sc[0], sc[1])
    best[s0] = F[l][sc]
    heapq.heappush(pq, (-F[l][sc], s0))
goal = (1, tc[0], tc[1])
while pq:
    neg, p = heapq.heappop(pq)
    v = -neg
    if v < best.get(p, -9.9) - 1e-9:
        continue
    if p == goal:
        break
    l, iy, ix = p
    for l2 in range(3):
        if l2 != l:
            q = (l2, iy, ix)
            nv = min(v, VIAF[iy, ix] - 0.25 + F[l2][iy, ix] * 0)  # via cap
            nv = min(v, VIAF[iy, ix])
            if nv > best.get(q, -9.9) + 1e-9:
                best[q] = nv
                prev[q] = p
                heapq.heappush(pq, (-nv, q))
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            jy, jx = iy + dy, ix + dx
            if not (0 <= jy < NY and 0 <= jx < NX):
                continue
            q = (l, jy, jx)
            nv = min(v, F[l][jy, jx])
            if nv > best.get(q, -9.9) + 1e-9:
                best[q] = nv
                prev[q] = p
                heapq.heappush(pq, (-nv, q))
print('widest (field units; track needs >= +0.10):', round(best[goal], 3))
path, p = [], goal
while p in prev:
    path.append(p)
    p = prev[p]
path.append(p)
path.reverse()
bn = min(path, key=lambda p: F[p[0]][p[1], p[2]] if p[0] == goal[0]
         or True else 9)
# bottleneck along path by effective value
vals = []
for p in path:
    l, iy, ix = p
    vals.append((F[l][iy, ix], p))
vals.sort(key=lambda t: t[0])
for v, p in vals[:4]:
    l, iy, ix = p
    print(f'  L{l} ({fxs[ix]:.2f},{fys[iy]:.2f}) field {v:+.3f} '
          f'binder {ARG[l][iy, ix]}')
layers_used = sorted({p[0] for p in path})
print('path layers:', layers_used, 'path states:', len(path))
print('done')
