"""t_au23: diagnose the SCL chord block in the au21 model (DATA entry
placed). Maximin (widest) search on In2 from SCL via (69.35,1.40) to
anchor (67.875,5.125); report bottleneck value + location + binder.
Also widest on F and B for the same endpoints."""
import wx
_app = wx.App(False)
import sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
import importlib.util
spec = importlib.util.spec_from_file_location(
    'chain', 'scratch/work/au/t_au21_chain.py')
# cannot exec chain (it runs A*); rebuild model by copying its top part
src = open('scratch/work/au/t_au21_chain.py').read()
head = src.split('# ---- fine A* machinery')[0]
g = {'__name__': 'chaindata'}
exec(head, g)
pool = g['pool']
# add DATA entry journey
jd = json.load(open('scratch/work/au/entry_au21_DATA.json'))
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
for LAYER in (1, 0, 2):
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
    # maximin
    NY, NX = f.shape
    sc = (int(round((1.40 - FY0) / FST)), int(round((69.35 - FX0) / FST)))
    tc = (int(round((5.125 - FY0) / FST)), int(round((67.875 - FX0) / FST)))
    best = np.full(f.shape, -9.9)
    best[sc] = f[sc]
    pq = [(-f[sc], sc)]
    prev = {}
    while pq:
        neg, p = heapq.heappop(pq)
        v = -neg
        if v < best[p] - 1e-9:
            continue
        if p == tc:
            break
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                q = (p[0] + dy, p[1] + dx)
                if not (0 <= q[0] < NY and 0 <= q[1] < NX):
                    continue
                nv = min(v, f[q])
                if nv > best[q] + 1e-9:
                    best[q] = nv
                    prev[q] = p
                    heapq.heappush(pq, (-nv, q))
    print(f'L{LAYER}: start field {f[sc]:+.3f}, goal field {f[tc]:+.3f}, '
          f'widest to goal {best[tc]:+.3f}')
    # walk back, find bottleneck cell
    if best[tc] > -9:
        path, p = [], tc
        while p != sc:
            path.append(p)
            p = prev[p]
        path.append(sc)
        bn = min(path, key=lambda p: f[p])
        print(f'   bottleneck at ({fxs[bn[1]]:.2f},{fys[bn[0]]:.2f}) '
              f'field {f[bn]:+.3f} binder: {arg[bn]}')
print('done')
