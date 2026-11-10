"""scan_debug: why does DIR fail? Sample the CURRENT built DIR
journey against the scan raster; run DIR alone; bisect which
item class blocks the journey samples."""
import math
import sys

sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/bd')
import gridroute as GR
from scan_rst import (ALL4, BOARD, DIST, GND_NOW, TERM, build_base,
                      classify, free_cell, near_district)

items = GR.load_items(BOARD, keep=near_district)
fixed, kept, relay = classify(items)
base10 = build_base(fixed, 0.10)

# current DIR journey (exp257, pass 219)
JOURNEY = [
    ('F', (75.75, 16.875)), ('F', (75.60, 17.30)), ('F', (75.42, 17.95)),
    ('VIA', (74.82, 18.10)),
    ('B', (74.82, 18.10)), ('B', (73.30, 18.42)), ('B', (71.375, 19.125)),
]


def sample(raster):
    bad = []
    for (L, (x, y)) in JOURNEY:
        i, j = raster.cell(x, y)
        if L == 'VIA':
            if raster.via[j, i]:
                bad.append(('VIA', x, y))
        elif raster.track[L][j, i]:
            bad.append((L, x, y))
    return bad


r = base10.copy()
r.add_item(GR.Item('GND', 'via', a=GND_NOW, hw=0.25))
for other in ALL4:
    if other != 'ULPI_DIR':
        for it in kept[other]:
            r.add_item(it, routed_hw=0.10)
print('journey samples blocked (DIR view):', sample(r))

# DIR alone via A*
s, g, hw = TERM['ULPI_DIR']
sc = free_cell(r, s[0], s[1], s[2])
gc = free_cell(r, g[0], g[1], g[2])
print('DIR start cell', sc, 'goal cell', gc)
path = GR.astar(r, (sc[0], sc[1], s[2]), (gc[0], gc[1], g[2]))
print('DIR alone:', 'PATH' if path else 'NO PATH')

# bisect: stamp fixed items net by net, find blockers of journey
from collections import defaultdict
by_net = defaultdict(list)
for it in fixed:
    by_net[it.net].append(it)
culprits = []
for net, its in by_net.items():
    rr = GR.Raster(DIST[0], DIST[1], DIST[2], DIST[3], pitch=0.05,
                   eps=0.02, routed_hw=0.10)
    for it in its:
        rr.add_item(it)
    b = sample(rr)
    if b:
        culprits.append((net, b))
for other in ALL4:
    if other == 'ULPI_DIR':
        continue
    rr = GR.Raster(DIST[0], DIST[1], DIST[2], DIST[3], pitch=0.05,
                   eps=0.02, routed_hw=0.10)
    for it in kept[other]:
        rr.add_item(it, routed_hw=0.10)
    b = sample(rr)
    if b:
        culprits.append((f'kept:{other}', b))
print('blockers by net:')
for c in culprits:
    print(' ', c)
