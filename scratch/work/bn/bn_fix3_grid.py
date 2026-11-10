#!/usr/bin/env python3
"""bn fix3 grid (parent-driven): joint via placement for the D2-D6 knot
on exp271. Prices d0.5 via candidates for D2/D3/D5/D6 against the
exp271 pool with the knot nets' own copper removed (their fans re-lay),
D4's via kept as a fixed obstacle, KiCad pricing (0.20 flat). Then
filters joint tuples on pairwise via-via >= 0.70."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
import gridroute as G
import bm_gate as BG

BG.clr = lambda net: 0.20
SRC = 'hw/pdlvds_rx.exp271.kicad_pcb'
items = G.load_items(SRC)
VICTIMS = {'ULPI_D2', 'ULPI_D3', 'ULPI_D4', 'ULPI_D5', 'ULPI_D6'}
BOX = (77.5, 8.0, 84.5, 18.5)


def inbox(it):
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
    elif it.kind == 'via':
        cx, cy = it.a
    else:
        cx = (it.a[0] + it.b[0]) / 2; cy = (it.a[1] + it.b[1]) / 2
    return BOX[0] <= cx <= BOX[2] and BOX[1] <= cy <= BOX[3]


pool = []
for it in items:
    if it.kind == 'pad' and it.net in ('+3V3D', 'GND'):
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if abs(cx - 80.825) < 0.01 and abs(cy - 13.6) < 0.01:
            continue  # C48 pad1: replaced by 0402 rect below
        if abs(cx - 82.375) < 0.01 and abs(cy - 13.6) < 0.01:
            continue  # C48 pad2: replaced by 0402 rect below
    if it.net == '+3V3D' and it.kind == 'trk' and it.layer == 'F':
        a = (round(it.a[0], 3), round(it.a[1], 3))
        b = (round(it.b[0], 3), round(it.b[1], 3))
        if {a, b} == {(80.825, 13.6), (81.3, 13.0)}:
            continue  # only C48's F feed head re-lays; B highway STAYS
    
    if not inbox(it):
        continue
    if it.net in VICTIMS:
        if it.kind == 'via' and it.net == 'ULPI_D4':
            pool.append(it)          # D4's via: fixed obstacle
        continue                     # knot tracks + moving vias: removed
    pool.append(it)

pool.append(G.Item('+3V3D', 'pad', layer='F.Cu',
                     rect=(80.84, 13.29, 81.40, 13.91)))
pool.append(G.Item('GND', 'pad', layer='F.Cu',
                   rect=(81.80, 13.29, 82.36, 13.91)))

BOXES = {
    'ULPI_D2': (79.7, 12.2, 80.6, 13.7),
    'ULPI_D3': (79.8, 13.1, 80.6, 14.3),
    'ULPI_D4': (79.8, 13.9, 80.9, 14.9),
    'ULPI_D5': (79.8, 14.6, 80.95, 15.9),
    'ULPI_D6': (80.2, 14.7, 80.95, 15.45),
}
legal = {}
for net, (x0, y0, x1, y1) in BOXES.items():
    good = []
    xi = x0
    while xi <= x1 + 1e-9:
        yi = y0
        while yi <= y1 + 1e-9:
            pt = (round(xi, 3), round(yi, 3))
            m = min((mm for mm, _ in BG.margin_via(pt, net, pool)),
                    default=9)
            if m >= 0:
                good.append((pt[0], pt[1], round(m, 3)))
            yi += 0.05
        xi += 0.05
    legal[net] = good
    print(net, 'spots:', [(g[0], g[1]) for g in good])
    print(net, 'legal', len(good), 'of',
          int((x1 - x0) / 0.05 + 1) * int((y1 - y0) / 0.05 + 1))

# joint tuples for D4/D5/D6 (D2/D3 reported separately)
import itertools


def compat(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 >= 0.49


best = []
for d4 in legal['ULPI_D4']:
    for d5 in legal['ULPI_D5']:
        if not compat(d4, d5):
            continue
        for d6 in legal['ULPI_D6']:
            if not (compat(d6, d4) and compat(d6, d5)):
                continue
            pts = [d4, d5, d6]
            worst = min(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 - 0.70
                        for a, b in itertools.combinations(pts, 2))
            score = min(worst, min(p[2] for p in pts))
            best.append((round(score, 3), d4, d5, d6))
best.sort(reverse=True)
print('D4/D5/D6 joint tuples:', len(best))
for row in best[:15]:
    print(row)
