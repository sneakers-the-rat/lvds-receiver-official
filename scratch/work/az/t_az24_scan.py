"""t_az24: exact legal d0.5 via scan for XI on the faithful pool.
A via at (x,y) is legal iff item_margin >= 0 on ALL layers vs all
foreign items (pads/segs/vias), where the via item carries the
layer's own representation (same disc on F/In2/B).
Scan x[70.5,77.0] y[8.5,13.5] step 0.05; print legal sites grouped,
plus the best (max-min-margin) sites in the south band.
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')


def via_margin(x, y):
    v = ('via', 'XI', (x, y, 0.25), 0.2)
    m = 9.9
    for l in range(3):
        for o in pool[l]:
            if o[1] == 'XI':
                continue
            mm = item_margin(l, v, [o])
            if mm < m:
                m = mm
    return m


legal = []
best = []
import numpy as np
for xi in range(141):
    x = 70.5 + xi * 0.05
    for yi in range(101):
        y = 8.5 + yi * 0.05
        m = via_margin(round(x, 3), round(y, 3))
        if m >= 0.0:
            legal.append((round(x, 2), round(y, 2), round(m, 3)))
        best.append((round(m, 3), round(x, 2), round(y, 2)))
best.sort(reverse=True)
print('legal d0.5 via sites:', len(legal))
rows = {}
for (x, y, m) in legal:
    rows.setdefault(y, []).append(x)
for y in sorted(rows):
    xs = rows[y]
    print(f'  y={y}: x {min(xs)}..{max(xs)} n={len(xs)}')
print('top-15 near-legal (margin, x, y):')
for b in best[:15]:
    print('  ', b)
print('=== done ===')
