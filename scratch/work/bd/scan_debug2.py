"""scan_debug2: dense-sample the built DIR journey segments
against the DIR-view raster; for each blocked sample, name the
net whose stamps block it (per-net rasters)."""
import math
import sys
from collections import defaultdict

sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/bd')
import gridroute as GR
from scan_rst import (ALL4, BOARD, DIST, GND_NOW, build_base,
                      classify, near_district)

items = GR.load_items(BOARD, keep=near_district)
fixed, kept, relay = classify(items)
base10 = build_base(fixed, 0.10)

SEGS = [
    ('F', (75.75, 16.875), (75.60, 17.30)),
    ('F', (75.60, 17.30), (75.42, 17.95)),
    ('F', (75.42, 17.95), (74.82, 18.10)),
    ('B', (74.82, 18.10), (73.30, 18.42)),
    ('B', (73.30, 18.42), (71.375, 19.125)),
]
VIA = (74.82, 18.10)


def dense_pts():
    pts = []
    for (L, a, b) in SEGS:
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.025))
        for k in range(n + 1):
            t = k / n
            pts.append((L, (a[0] + t * (b[0] - a[0]),
                            a[1] + t * (b[1] - a[1]))))
    return pts


def blocked_set(raster, pts):
    out = []
    for (L, (x, y)) in pts:
        i, j = raster.cell(x, y)
        if raster.track[L][j, i]:
            out.append((L, round(x, 2), round(y, 2)))
    i, j = raster.cell(*VIA)
    if raster.via[j, i]:
        out.append(('VIA', VIA[0], VIA[1]))
    return out


r = base10.copy()
r.add_item(GR.Item('GND', 'via', a=GND_NOW, hw=0.25))
for other in ALL4:
    if other != 'ULPI_DIR':
        for it in kept[other]:
            r.add_item(it, routed_hw=0.10)
pts = dense_pts()
bad = blocked_set(r, pts)
print(f'dense blocked samples: {len(bad)} of {len(pts) + 1}')
for b in bad[:40]:
    print('  ', b)

# per-net attribution for the blocked samples
by_net = defaultdict(list)
for it in fixed:
    by_net[it.net].append(it)
for net, its in by_net.items():
    rr = GR.Raster(DIST[0], DIST[1], DIST[2], DIST[3], pitch=0.05,
                   eps=0.02, routed_hw=0.10)
    for it in its:
        rr.add_item(it)
    b = blocked_set(rr, pts)
    if b:
        print(f'fixed net {net}: blocks {len(b)} e.g. {b[:4]}')
for other in ALL4:
    if other == 'ULPI_DIR':
        continue
    rr = GR.Raster(DIST[0], DIST[1], DIST[2], DIST[3], pitch=0.05,
                   eps=0.02, routed_hw=0.10)
    for it in kept[other]:
        rr.add_item(it, routed_hw=0.10)
    b = blocked_set(rr, pts)
    if b:
        print(f'kept {other}: blocks {len(b)} e.g. {b[:4]}')
rr = GR.Raster(DIST[0], DIST[1], DIST[2], DIST[3], pitch=0.05,
               eps=0.02, routed_hw=0.10)
rr.add_item(GR.Item('GND', 'via', a=GND_NOW, hw=0.25))
b = blocked_set(rr, pts)
if b:
    print(f'GND via candidate: blocks {len(b)} e.g. {b[:4]}')
