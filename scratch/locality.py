#!/usr/bin/env python3
"""Connectivity-locality census: per-net star length (sum of pad
distances to the net's pad centroid, mm) and span (max pairwise pad
distance); per-part mean distance from each of its pads to the nearest
partner pad (different footprint, same net). Power/ground nets with
>40 pads (GND) are reported but excluded from the star total.

Usage: python3 scratch/locality.py BOARD.kicad_pcb
"""
import sys, math
from collections import defaultdict
import pcbnew

MM = 1_000_000
b = pcbnew.LoadBoard(sys.argv[1])

net_pads = defaultdict(list)   # net -> [(ref, x, y)]
part_pads = defaultdict(list)  # ref -> [(net, x, y)]
for fp in b.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        net = pad.GetNetname()
        if not net:
            continue
        p = pad.GetPosition()
        x, y = p.x / MM, p.y / MM
        net_pads[net].append((ref, x, y))
        part_pads[ref].append((net, x, y))

def star_span(pads):
    cx = sum(p[1] for p in pads) / len(pads)
    cy = sum(p[2] for p in pads) / len(pads)
    star = sum(math.hypot(p[1] - cx, p[2] - cy) for p in pads)
    span = 0.0
    for i in range(len(pads)):
        for j in range(i + 1, len(pads)):
            d = math.hypot(pads[i][1] - pads[j][1], pads[i][2] - pads[j][2])
            span = max(span, d)
    return star, span

rows = []
total_star = 0.0
for net, pads in net_pads.items():
    refs = set(p[0] for p in pads)
    if len(pads) < 2 or len(refs) < 2:
        continue
    s, sp = star_span(pads)
    rows.append((net, len(pads), s, sp))
    if len(pads) <= 40:
        total_star += s
rows.sort(key=lambda r: -r[2])
print(f'TOTAL star (nets with <=40 pads): {total_star:.0f} mm over {len(rows)} multi-part nets')
print('\nTop nets by star length:')
print(f'{"net":28s} {"pads":>5} {"star":>8} {"span":>7}')
for net, n, s, sp in rows[:18]:
    print(f'{net:28s} {n:5d} {s:8.0f} {sp:7.1f}')

# per-part: mean distance to nearest partner pad, over pads whose net
# has a partner; also the max
part_rows = []
for ref, pads in part_pads.items():
    ds = []
    for net, x, y in pads:
        best = None
        for (r2, x2, y2) in net_pads[net]:
            if r2 == ref:
                continue
            d = math.hypot(x - x2, y - y2)
            if best is None or d < best:
                best = d
        if best is not None:
            ds.append(best)
    if ds:
        part_rows.append((ref, sum(ds) / len(ds), max(ds), len(ds)))
part_rows.sort(key=lambda r: -r[1])
print('\nTop parts by MEAN distance to nearest partner pad:')
print(f'{"part":8s} {"mean":>7} {"max":>7} {"pads":>5}')
for ref, mean, mx, n in part_rows[:20]:
    print(f'{ref:8s} {mean:7.1f} {mx:7.1f} {n:5d}')
far = sum(1 for _, pads in part_pads.items()
          for net, x, y in pads
          if any(r2 != _ for r2, _, _ in net_pads[net]) and
          min((math.hypot(x - x2, y - y2) for r2, x2, y2 in net_pads[net] if r2 != _), default=0) > 40)
print(f'\nPads whose nearest partner is >40 mm away: {far}')
