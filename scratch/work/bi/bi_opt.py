#!/usr/bin/env python3
"""bi micro-optimizer: RST dive FIXED at grid winner (74.85,17.45) d0.5.
Independently score DIR-via and NXT-via candidate positions (with their
escape polylines) vs the south-box pool (stock DIR/NXT escapes ripped),
then combine top candidates with pairwise checks. Referee rules."""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bi')
import gridroute as G
from bi_price import m_via, m_trk, BASE

BOX = (72.8, 15.8, 76.6, 20.6)


def near(p, q, tol=0.006):
    return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol


def in_box(it):
    x0, y0, x1, y1 = BOX
    if it.kind == 'via':
        return x0 <= it.a[0] <= x1 and y0 <= it.a[1] <= y1
    if it.kind == 'trk':
        return not (max(it.a[0], it.b[0]) < x0 or min(it.a[0], it.b[0]) > x1 or
                    max(it.a[1], it.b[1]) < y0 or min(it.a[1], it.b[1]) > y1)
    r = it.rect
    return not (r[2] < x0 or r[0] > x1 or r[3] < y0 or r[1] > y1)


RIP_TRK = [
    ('ULPI_CK', 'F', (75.125, 5.875), (75.250, 5.162)),
    ('ULPI_DIR', 'F', (75.750, 16.875), (75.600, 17.300)),
    ('ULPI_DIR', 'F', (75.600, 17.300), (75.420, 17.950)),
    ('ULPI_DIR', 'F', (75.420, 17.950), (74.820, 18.100)),
    ('ULPI_DIR', 'B', (74.820, 18.100), (73.300, 18.420)),
    ('ULPI_NXT', 'F', (75.250, 16.875), (74.940, 17.360)),
    ('ULPI_NXT', 'In2', (74.940, 17.360), (74.100, 17.700)),
    ('ULPI_NXT', 'In2', (74.100, 17.700), (74.500, 19.250)),
]
RIP_VIA = [('ULPI_DIR', (74.820, 18.100)), ('ULPI_NXT', (74.940, 17.360))]
pool = []
for it in BASE:
    if not in_box(it):
        continue
    if it.kind == 'trk' and any(it.net == n and it.layer == l and
                                ((near(it.a, a) and near(it.b, b)) or (near(it.a, b) and near(it.b, a)))
                                for n, l, a, b in RIP_TRK):
        continue
    if it.kind == 'via' and any(it.net == n and near(it.a, at) for n, at in RIP_VIA):
        continue
    pool.append(it)
print('pool items:', len(pool))

RST_DIVE = (74.85, 17.45)
rst_items = [G.Item('USB_RST', 'via', a=RST_DIVE, hw=0.25),
             G.Item('USB_RST', 'trk', layer='F', a=(74.25, 16.878), b=RST_DIVE, hw=0.10)]
pool_rst = pool + rst_items


def worst_of(cands, poolx):
    out = []
    for kind, net, layer, a, b, hw in cands:
        if kind == 'via':
            r = m_via(a, hw, net, poolx)
        else:
            r = m_trk(a, b, layer, hw, net, poolx)
        out += [(m, d) for m, d in r[:1]]
    return sorted(out)


def T(net, layer, a, b, w=0.2):
    return ('trk', net, layer, a, b, w / 2)


def V(net, x, y, d=0.5):
    return ('via', net, None, (x, y), None, d / 2)


def dir_set(v):
    return [V('ULPI_DIR', v[0], v[1]),
            T('ULPI_DIR', 'F', (75.75, 16.875), (75.60, 17.30)),
            T('ULPI_DIR', 'F', (75.60, 17.30), (75.42, 17.95)),
            T('ULPI_DIR', 'F', (75.42, 17.95), v),
            T('ULPI_DIR', 'B', v, (73.30, 18.42))]


def nxt_set(v):
    join = (74.10, 17.70) if v[1] < 18.6 else (74.50, 19.25)
    return [V('ULPI_NXT', v[0], v[1]),
            T('ULPI_NXT', 'F', (75.25, 16.875), v),
            T('ULPI_NXT', 'In2', v, join)]


def grid_set(fn, xs, ys, poolx):
    res = []
    y = ys[0]
    while y <= ys[1] + 1e-9:
        x = xs[0]
        while x <= xs[1] + 1e-9:
            v = (round(x, 2), round(y, 2))
            w = worst_of(fn(v), poolx)
            res.append((w[0][0], v, w[0][1]))
            x += 0.05
        y += 0.05
    res.sort(reverse=True)
    return res


dirs = grid_set(dir_set, (74.55, 75.05), (17.95, 18.50), pool_rst)
nxts = grid_set(nxt_set, (74.90, 75.60), (16.95, 18.30), pool_rst)
nxts += grid_set(nxt_set, (74.55, 75.20), (18.65, 19.40), pool_rst)
nxts.sort(reverse=True)
print('DIR top5:')
for s, v, d in dirs[:5]:
    print(f'   {s:+.3f} @{v} :: {d}')
print('NXT top5:')
for s, v, d in nxts[:5]:
    print(f'   {s:+.3f} @{v} :: {d}')
best = None
for sd, vd, _ in dirs[:25]:
    for sn, vn, _ in nxts[:25]:
        # pairwise: DIR set vs NXT set
        poolx = pool_rst + [G.Item(i[1], i[0], layer=i[2], a=i[3], b=i[4], hw=i[5])
                            for i in dir_set(vd) if i[0] == 'trk'] + \
                [G.Item('ULPI_DIR', 'via', a=vd, hw=0.25)]
        w = worst_of(nxt_set(vn), poolx)
        tot = min(sd, sn, w[0][0])
        if best is None or tot > best[0]:
            best = (tot, vd, vn, w[0][1])
print(f'BEST COMBO: worst {best[0]:+.3f} DIR@{best[1]} NXT@{best[2]} :: {best[3]}')
