#!/usr/bin/env python3
"""D5/D6 via pair grid for the exp270 east D-fan knot, KiCad pricing
(0.20 flat — the board's only netclass rule; check_pcb power/buried
bands are census, not DRC). Prices every (D5 via, D6 via) pair on a
0.05 grid: each via vs all board items (victim-filtered per bn_fix2),
via-via >= 0.70 centres. Reports the best pairs by worst margin."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bn')
import gridroute as G
import bn_fix2 as F

items = G.load_items(F.SRC)
for it in items:
    it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
new_pads, centres = F.moved_pad_items()
pool = []
for it in items:
    if F.is_victim(it):
        continue
    if it.kind == 'pad' and any(abs((it.rect[0] + it.rect[2]) / 2 - cx) < 1.05 and
                                abs((it.rect[1] + it.rect[3]) / 2 - cy) < 1.05
                                for cx, cy in centres):
        continue
    pool.append(it)
pool += new_pads

import bm_gate as BG
BG.clr = lambda net: 0.20  # KiCad pricing


def via_worst(c, net):
    ms = BG.margin_via(c, net, pool, r=0.25)
    return ms[0] if ms else (9.9, 'none')


def grid(x0, x1, y0, y1, net):
    out = []
    n = int(round((x1 - x0) / 0.05))
    m = int(round((y1 - y0) / 0.05))
    for i in range(n + 1):
        for j in range(m + 1):
            c = (round(x0 + i * 0.05, 2), round(y0 + j * 0.05, 2))
            w, d = via_worst(c, net)
            out.append((w, c, d))
    return sorted(out, reverse=True)


d5 = grid(79.9, 80.7, 14.9, 15.6, 'ULPI_D5')
d6 = grid(80.3, 81.0, 14.5, 15.2, 'ULPI_D6')
print('D5 legal spots (margin>=0):', sum(1 for w, _, _ in d5 if w >= 0), '/', len(d5))
print('D6 legal spots (margin>=0):', sum(1 for w, _, _ in d6 if w >= 0), '/', len(d6))
print('D5 top5:', [(round(w, 3), c) for w, c, _ in d5[:5]])
print('D6 top5:', [(round(w, 3), c) for w, c, _ in d6[:5]])
pairs = []
for w5, c5, _ in d5:
    if w5 < -0.05:
        continue
    for w6, c6, _ in d6:
        if w6 < -0.05:
            continue
        import math
        dvv = math.hypot(c5[0] - c6[0], c5[1] - c6[1]) - 0.70
        pairs.append((min(w5, w6, dvv), c5, c6, round(w5, 3), round(w6, 3), round(dvv, 3)))
pairs.sort(reverse=True)
print('pairs (worst-margin, D5, D6, w5, w6, via-via):')
for p in pairs[:12]:
    print('  ', p)
