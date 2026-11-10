#!/usr/bin/env python3
"""Search D2/D3 configurations for the bn_fix3 knot build.

D4 is kept whole; D5/D6/+3V3D are fixed at the analysed values below.
Variables: D2 via V2, D2 feed (direct or 1 bow vertex), D2 head
(straight to the existing far via (80.0,8.3)); D3 via V3, D3 stub,
D3 legs (straight or 1 bow vertex) to the chain join (82.2,11.6).
Scoring: bn_fix3's own gate machinery (bm_gate margins, KiCad 0.20
flat) against the victim-filtered pool, plus new-vs-new among all new
items. Local pool = items within the district bbox (distant items
cannot produce margins below the cap)."""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bn')
import gridroute as G
import bm_gate as BG
import bn_fix3 as F3

BG.clr = lambda net: 0.20
CAP = 0.30  # scores are capped; only accuracy near/below this matters

# ---- fixed new items (D5, D6, +3V3D) as NN obstacles ----
FIXED_TRK = [
    ('ULPI_D5', 'F.Cu', (79.19, 14.75), (80.35, 15.3), 0.1),
    ('ULPI_D5', 'In2.Cu', (80.35, 15.3), (81.95, 15.65), 0.125),
    ('ULPI_D5', 'In2.Cu', (81.95, 15.65), (82.0, 15.3), 0.125),
    ('ULPI_D6', 'F.Cu', (79.438, 15.25), (78.9, 16.3), 0.1),
    ('ULPI_D6', 'F.Cu', (78.9, 16.3), (79.9, 16.28), 0.1),
    ('ULPI_D6', 'F.Cu', (79.9, 16.28), (80.68, 15.9), 0.1),
    ('ULPI_D6', 'F.Cu', (80.68, 15.9), (80.95, 15.3), 0.1),
    ('ULPI_D6', 'F.Cu', (80.95, 15.3), (80.85, 14.8), 0.1),
    ('ULPI_D6', 'In2.Cu', (80.85, 14.8), (81.375, 14.125), 0.125),
    ('+3V3D', 'F.Cu', (81.12, 13.6), (81.3, 13.0), 0.1),
]
FIXED_VIA = [('ULPI_D5', (80.35, 15.3)), ('ULPI_D6', (80.85, 14.8))]

# ---- pool (same construction as bn_fix3.gate) ----
items = G.load_items(F3.SRC)
for it in items:
    it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
pool = []
for it in items:
    if F3.is_victim(it):
        continue
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if any(abs(cx - ox) < 0.01 and abs(cy - oy) < 0.01 for ox, oy in F3.C48_OLD):
            continue
    pool.append(it)
for net, rect in F3.C48_NEW:
    pool.append(G.Item(net, 'pad', layer='F.Cu', rect=rect))

BOX = (78.3, 7.3, 83.2, 17.2)


def in_box(it):
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        return BOX[0] - 1 <= cx <= BOX[2] + 1 and BOX[1] - 1 <= cy <= BOX[3] + 1
    pts = [it.a] + ([it.b] if it.kind == 'trk' else [])
    return any(BOX[0] - 1 <= x <= BOX[2] + 1 and BOX[1] - 1 <= y <= BOX[3] + 1
               for x, y in pts)


lpool = [it for it in pool if in_box(it)]
print(f'pool {len(pool)} -> local {len(lpool)}')


def min_margin_trk(a, b, layer, net, hw):
    ms = BG.margin_trk(a, b, layer, net, lpool, hw=hw)
    return min([m for m, d in ms], default=9.9)


def min_margin_via(at, net):
    ms = BG.margin_via(at, net, lpool, r=0.25)
    return min([m for m, d in ms], default=9.9)


def nn_trk_trk(s1, s2):
    n1, l1, a, b, h1 = s1
    n2, l2, c, d, h2 = s2
    if n1 == n2 or l1 != l2:
        return 9.9
    return BG.seg_seg(a, b, c, d) - h1 - h2 - 0.20


def nn_trk_via(s, v):
    n1, l1, a, b, h1 = s
    n2, c = v
    if n1 == n2:
        return 9.9
    return BG.pt_seg(c, a, b) - h1 - 0.25 - 0.20


def score_option(trks, vias):
    """trks: (net, layer, a, b, hw); vias: (net, at). Returns min margin
    vs pool and vs FIXED items."""
    sc = 9.9
    for nn, ll, a, b, hw in trks:
        sc = min(sc, min_margin_trk(a, b, ll, nn, hw))
        for fs in FIXED_TRK:
            sc = min(sc, nn_trk_trk((nn, ll, a, b, hw), fs))
        for fv in FIXED_VIA:
            sc = min(sc, nn_trk_via((nn, ll, a, b, hw), fv))
    for nn, at in vias:
        sc = min(sc, min_margin_via(at, nn))
        for fs in FIXED_TRK:
            sc = min(sc, nn_trk_via(fs, (nn, at)))
    return sc


def grid(x0, x1, y0, y1, step):
    pts = []
    x = x0
    while x <= x1 + 1e-9:
        y = y0
        while y <= y1 + 1e-9:
            pts.append((round(x, 3), round(y, 3)))
            y += step
        x += step
    return pts


# ---- D3 options ----
print('scoring D3 options...')
d3_opts = []
v3_cands = [p for p in grid(79.7, 80.8, 13.3, 14.2, 0.05)
            if min_margin_via(p, 'ULPI_D3') >= 0.005]
v3_cands += [(79.95, 13.75), (79.93, 13.73), (79.9, 13.75)]
v3_cands = sorted(set(v3_cands))
print(f'  V3 candidates: {len(v3_cands)}')
bow3 = grid(80.3, 81.7, 12.2, 13.3, 0.15)
for v3 in v3_cands:
    vm = min_margin_via(v3, 'ULPI_D3')
    paths = [[(v3, (82.2, 11.6))]]
    for b in bow3:
        paths.append([(v3, b), (b, (82.2, 11.6))])
    scored = []
    for path in paths:
        trks = [('ULPI_D3', 'In2.Cu', a, b, 0.125) for a, b in path]
        if v3 != (79.95, 13.75):
            trks.append(('ULPI_D3', 'F.Cu', (79.95, 13.75), v3, 0.1))
        sc = min(vm, score_option(trks, [('ULPI_D3', v3)]))
        scored.append((sc, trks))
    scored.sort(key=lambda t: -t[0])
    for sc, trks in scored[:2]:
        if sc >= 0.005:
            d3_opts.append((sc, v3, trks))
print(f'  D3 options kept: {len(d3_opts)}')

# ---- D2 options ----
print('scoring D2 options...')
d2_opts = []
v2_cands = [p for p in grid(79.7, 80.8, 12.2, 13.5, 0.05)
            if min_margin_via(p, 'ULPI_D2') >= 0.005]
v2_cands += [(80.28, 12.95)]
v2_cands = sorted(set(v2_cands))
print(f'  V2 candidates: {len(v2_cands)}')
bow2 = grid(79.5, 80.5, 12.3, 13.3, 0.1)
for v2 in v2_cands:
    vm = min_margin_via(v2, 'ULPI_D2')
    head = ('ULPI_D2', 'In2.Cu', v2, (80.0, 8.3), 0.125)
    hm = score_option([head], [])
    if hm < 0.005:
        continue
    feeds = [[(79.438, 13.25), v2]]
    for b in bow2:
        feeds.append([(79.438, 13.25), b, v2])
    scored = []
    for feed in feeds:
        trks = [('ULPI_D2', 'F.Cu', feed[i], feed[i + 1], 0.1)
                for i in range(len(feed) - 1)] + [head]
        sc = min(vm, hm, score_option(trks, [('ULPI_D2', v2)]))
        scored.append((sc, trks))
    scored.sort(key=lambda t: -t[0])
    for sc, trks in scored[:2]:
        if sc >= 0.005:
            d2_opts.append((sc, v2, trks))
print(f'  D2 options kept: {len(d2_opts)}')

# ---- combine ----
print('combining...')
best = []
for sc3, v3, t3 in d3_opts:
    for sc2, v2, t2 in d2_opts:
        sc = min(sc3, sc2)
        if sc < 0.005:
            continue
        m = math.hypot(v3[0] - v2[0], v3[1] - v2[1]) - 0.5 - 0.20
        sc = min(sc, m)
        if sc < 0.005:
            continue
        for s in t3:
            sc = min(sc, nn_trk_via(s, ('ULPI_D2', v2)))
            for s2 in t2:
                sc = min(sc, nn_trk_trk(s, s2))
        for s in t2:
            sc = min(sc, nn_trk_via(s, ('ULPI_D3', v3)))
        if sc >= 0.005:
            best.append((sc, v2, t2, v3, t3))
best.sort(key=lambda t: -t[0])
print(f'joint options: {len(best)}')
for sc, v2, t2, v3, t3 in best[:5]:
    print(f'\nSCORE {sc:+.3f}  V2={v2}  V3={v3}')
    for nn, ll, a, b, hw in t2 + t3:
        print(f'    ({nn!r}, {ll!r}, {a}, {b}, {hw * 2})')
