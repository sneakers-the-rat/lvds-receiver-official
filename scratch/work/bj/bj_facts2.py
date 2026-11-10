#!/usr/bin/env python3
"""bj facts 2: XO full geometry; In2 strip x[71.5,74.6] y[8.5,12.5];
F strip x[72.6,74.3] y[11.0,17.2]; In2 x[72.5,74.2] y[16.0,17.3];
+3V3A items near (73.625,10.625). Output -> bj_facts2_out.txt"""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
items = G.load_items(BOARD)
out = open('/home/hatch/workspace/pdlvds-route/scratch/work/bj/bj_facts2_out.txt', 'w')
P = lambda *a: print(*a, file=out)

def fmt(it):
    if it.kind == 'via':
        return f'VIA ({it.a[0]:.3f},{it.a[1]:.3f}) r{it.hw:.3f}'
    if it.kind == 'trk':
        return f'TRK[{it.layer}] ({it.a[0]:.3f},{it.a[1]:.3f})->({it.b[0]:.3f},{it.b[1]:.3f}) hw{it.hw:.3f}'
    return f'PAD[{it.layer}] rect({it.rect[0]:.3f},{it.rect[1]:.3f})-({it.rect[2]:.3f},{it.rect[3]:.3f})'

P('==== XO (all)')
for it in items:
    if it.net == 'XO':
        P('  ', fmt(it))
P('==== +3V3A items with any point in x[72.8,76.0] y[9.8,12.6]')
for it in items:
    if it.net != '+3V3A':
        continue
    pts = [it.a] + ([it.b] if it.kind == 'trk' else [])
    if it.kind == 'pad':
        pts = [(it.rect[0], it.rect[1]), (it.rect[2], it.rect[3])]
    if any(72.8 <= x <= 76.0 and 9.8 <= y <= 12.6 for x, y in pts):
        P('  ', fmt(it))

def strip(title, layer, x0, x1, y0, y1, skip):
    P(f'==== {title}')
    seen = set()
    for it in items:
        if it.net in skip or it.kind == 'pad':
            continue
        if it.kind == 'trk' and it.layer != layer:
            continue
        xs = [it.a[0]] + ([it.b[0]] if it.kind == 'trk' else [])
        ys = [it.a[1]] + ([it.b[1]] if it.kind == 'trk' else [])
        if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1:
            continue
        s = f'{it.net} {fmt(it)}'
        if s not in seen:
            seen.add(s)
            P('  ', s)

strip('In2 strip x[71.5,74.6] y[8.5,12.5]', 'In2', 71.5, 74.6, 8.5, 12.5, ('XO', '+3V3A'))
strip('F strip x[72.6,74.3] y[11.0,17.2]', 'F', 72.6, 74.3, 11.0, 17.2, ())
strip('In2 strip x[72.5,74.2] y[16.0,17.3]', 'In2', 72.5, 74.2, 16.0, 17.3, ())
out.close()
print('done')
