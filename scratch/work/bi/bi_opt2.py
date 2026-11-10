#!/usr/bin/env python3
"""bi joint random search: RST/NXT/DIR dive vias + escape stubs in the
U7 south fanout. Pool = south-box items with all three escapes ripped.
Stubs modelled straight or 1-bend (south-first). Score = exact referee
min margin over all new items vs pool + cross pairs. Bounded: 1500
samples, seed fixed. Reports the best triple found."""
import math
import random
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bi')
import gridroute as G
from bi_price import m_via, m_trk, BASE

BOX = (73.6, 16.4, 76.4, 20.0)


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
    ('ULPI_DIR', 'F', (75.750, 16.875), (75.600, 17.300)),
    ('ULPI_DIR', 'F', (75.600, 17.300), (75.420, 17.950)),
    ('ULPI_DIR', 'F', (75.420, 17.950), (74.820, 18.100)),
    ('ULPI_DIR', 'B', (74.820, 18.100), (73.300, 18.420)),
    ('ULPI_NXT', 'F', (75.250, 16.875), (74.940, 17.360)),
    ('ULPI_NXT', 'In2', (74.940, 17.360), (74.100, 17.700)),
    ('ULPI_NXT', 'In2', (74.100, 17.700), (74.500, 19.250)),
]
RIP_VIA = [('ULPI_DIR', (74.820, 18.100)), ('ULPI_NXT', (74.940, 17.360)),
           ('ULPI_CK', (75.125, 5.875))]
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
print('pool items:', len(pool), flush=True)


def T(net, layer, a, b, w=0.2):
    return ('trk', net, layer, a, b, w / 2)


def V(net, x, y, d=0.5):
    return ('via', net, None, (x, y), None, d / 2)


def stub(net, pad, v, bend):
    if bend == 0:
        return [T(net, 'F', pad, v)]
    mid = (pad[0], pad[1] + bend)
    return [T(net, 'F', pad, mid), T(net, 'F', mid, v)]


def build(pR, pN, pD, bR, bN, bD):
    items = []
    items += stub('USB_RST', (74.25, 16.878), pR, bR)
    items.append(V('USB_RST', pR[0], pR[1], 0.40))
    items += stub('ULPI_NXT', (75.25, 16.875), pN, bN)
    items.append(V('ULPI_NXT', pN[0], pN[1], 0.5))
    join = (74.10, 17.70) if pN[1] < 18.6 else (74.50, 19.25)
    items.append(T('ULPI_NXT', 'In2', pN, join))
    items += stub('ULPI_DIR', (75.75, 16.875), pD, bD)
    items.append(V('ULPI_DIR', pD[0], pD[1], 0.5))
    items.append(T('ULPI_DIR', 'B', pD, (73.30, 18.42)))
    return items


def as_items(new):
    return [G.Item(n, k, layer=l, a=a, b=b, hw=hw) for k, n, l, a, b, hw in new]


def score(new):
    allp = pool + as_items(new)
    worst = 9.9
    fence = ''
    for kind, net, layer, a, b, hw in new:
        r = m_via(a, hw, net, allp) if kind == 'via' else m_trk(a, b, layer, hw, net, allp)
        if r and r[0][0] < worst:
            worst, fence = r[0][0], f'{net} {a}->{b}: {r[0][1]}'
    return worst, fence


random.seed(219)
best = (-9, None, '')
for i in range(1500):
    pR = (74.85 + random.uniform(-0.06, 0.06), 17.45 + random.uniform(-0.06, 0.06))
    pN = (random.uniform(74.90, 75.60), random.uniform(16.95, 19.35))
    pD = (random.uniform(74.55, 75.05), random.uniform(17.95, 18.55))
    bR = random.choice([0, 0.35])
    bN = random.choice([0, 0.35, 0.6])
    bD = random.choice([0, 0.35])
    s, f = score(build(pR, pN, pD, bR, bN, bD))
    if s > best[0]:
        best = (s, (pR, pN, pD, bR, bN, bD), f)
        print(f'  [{i}] {s:+.3f} R@{pR} N@{pN} D@{pD} bends {(bR, bN, bD)} :: {f}', flush=True)
print('BEST:', best)
