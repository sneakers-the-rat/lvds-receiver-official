#!/usr/bin/env python3
"""bk facts: exact BIST chain east of window + +3V3A via neighbourhood."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G
items = G.load_items('/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb')
print('== BIST_DRV In2 segs with a point in x[73.8,76.2] y[4.8,6.3]:')
for it in items:
    if it.net == 'BIST_DRV' and it.kind == 'trk' and it.layer == 'In2' and \
       (73.8 <= it.a[0] <= 76.2 and 4.8 <= it.a[1] <= 6.3 or 73.8 <= it.b[0] <= 76.2 and 4.8 <= it.b[1] <= 6.3):
        print(f'  {it.a}->{it.b} hw{it.hw}')
print('== +3V3A items touching (73.625,10.625) or in x[73.2,74.5] y[8.2,10.8] any layer:')
for it in items:
    if it.net != '+3V3A':
        continue
    if it.kind == 'via':
        print(f'  VIA {it.a} r{it.hw}')
    elif it.kind == 'trk':
        if (73.2 <= it.a[0] <= 74.5 and 8.2 <= it.a[1] <= 10.8) or (73.2 <= it.b[0] <= 74.5 and 8.2 <= it.b[1] <= 10.8):
            print(f'  TRK[{it.layer}] {it.a}->{it.b} hw{it.hw}')
print('== F items (any net) with a point in x[73.3,74.4] y[8.4,10.7]:')
for it in items:
    if it.kind == 'trk' and it.layer == 'F' and \
       ((73.3 <= it.a[0] <= 74.4 and 8.4 <= it.a[1] <= 10.7) or (73.3 <= it.b[0] <= 74.4 and 8.4 <= it.b[1] <= 10.7)):
        print(f'  {it.net} {it.a}->{it.b} hw{it.hw}')
    if it.kind == 'pad' and it.layer == 'F' and it.rect[0] < 74.4 and it.rect[2] > 73.3 and it.rect[1] < 10.7 and it.rect[3] > 8.4:
        print(f'  PAD {it.net} {it.rect}')
    if it.kind == 'via' and 73.3 <= it.a[0] <= 74.4 and 8.4 <= it.a[1] <= 10.7:
        print(f'  VIA {it.net} {it.a} r{it.hw}')
print('== B items (any net) with a point in x[73.2,73.8] y[8.3,10.8]:')
for it in items:
    if it.kind == 'trk' and it.layer == 'B' and \
       ((73.2 <= it.a[0] <= 73.8 and 8.3 <= it.a[1] <= 10.8) or (73.2 <= it.b[0] <= 73.8 and 8.3 <= it.b[1] <= 10.8)):
        print(f'  {it.net} {it.a}->{it.b} hw{it.hw}')
