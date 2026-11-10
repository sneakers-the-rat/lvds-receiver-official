#!/usr/bin/env python3
"""bj facts: full geometry of DM_PHY / ULPI_DIR / ULPI_NXT / RBIAS /
ULPI_CK board-wide; all items in the south fanout box; In2+B items in
the journey box. Output -> bj_facts_out.txt"""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
items = G.load_items(BOARD)
out = open('/home/hatch/workspace/pdlvds-route/scratch/work/bj/bj_facts_out.txt', 'w')
P = lambda *a: print(*a, file=out)

def fmt(it):
    if it.kind == 'via':
        return f'VIA ({it.a[0]:.3f},{it.a[1]:.3f}) r{it.hw:.3f}'
    if it.kind == 'trk':
        return f'TRK[{it.layer}] ({it.a[0]:.3f},{it.a[1]:.3f})->({it.b[0]:.3f},{it.b[1]:.3f}) hw{it.hw:.3f}'
    return f'PAD[{it.layer}] rect({it.rect[0]:.3f},{it.rect[1]:.3f})-({it.rect[2]:.3f},{it.rect[3]:.3f})'

for net in ('DM_PHY', 'ULPI_DIR', 'ULPI_NXT', 'RBIAS', 'ULPI_CK'):
    P(f'==== {net} (all items)')
    for it in items:
        if it.net == net:
            P('  ', fmt(it))

P('==== SOUTH BOX x[72.8,77.2] y[15.5,20.2] all items (other nets)')
for it in items:
    if it.net in ('DM_PHY', 'ULPI_DIR', 'ULPI_NXT', 'RBIAS', 'ULPI_CK'):
        continue
    cx = it.a[0] if it.kind != 'pad' else (it.rect[0] + it.rect[2]) / 2
    cy = it.a[1] if it.kind != 'pad' else (it.rect[1] + it.rect[3]) / 2
    if it.kind == 'trk':
        cx = min(cx, it.b[0]); cy = min(cy, it.b[1])
        ex = max(it.a[0], it.b[0]); ey = max(it.a[1], it.b[1])
        if ex < 72.8 or cx > 77.2 or ey < 15.5 or cy > 20.2:
            continue
    elif not (72.8 <= cx <= 77.2 and 15.5 <= cy <= 20.2):
        continue
    P(f'  {it.net:12s}', fmt(it))

P('==== JOURNEY BOX x[72.8,76.4] y[4.5,17.0] In2 trks + B trks + vias (other nets)')
for it in items:
    if it.net in ('DM_PHY', 'ULPI_DIR', 'ULPI_NXT', 'RBIAS', 'ULPI_CK'):
        continue
    if it.kind == 'pad':
        continue
    if it.kind == 'trk' and it.layer not in ('In2', 'B'):
        continue
    xs = [it.a[0]] + ([it.b[0]] if it.kind == 'trk' else [])
    ys = [it.a[1]] + ([it.b[1]] if it.kind == 'trk' else [])
    if max(xs) < 72.8 or min(xs) > 76.4 or max(ys) < 4.5 or min(ys) > 17.0:
        continue
    P(f'  {it.net:12s}', fmt(it))
out.close()
print('done')
