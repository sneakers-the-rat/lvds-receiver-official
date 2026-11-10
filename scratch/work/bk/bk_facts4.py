#!/usr/bin/env python3
"""bk facts 4: NXT continuation north of (74.5,19.25); fanout zone all layers."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

items = G.load_items('/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb')
out = []
out.append('== ULPI_NXT all items with any point y>18.9 ==')
for it in items:
    if it.net != 'ULPI_NXT':
        continue
    pts = [it.a, it.b] if it.kind == 'trk' else [it.a]
    if it.kind == 'pad':
        out.append(f'NXT PAD[{it.layer}] {it.rect}')
    elif any(p[1] > 18.9 for p in pts):
        out.append(f'NXT {it.kind}[{it.layer}] {it.a} {it.b if it.kind == "trk" else ""} hw{it.hw}')
out.append('== zone x[72.9,76.1] y[18.3,20.8] all nets/layers ==')
for it in items:
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if 72.9 <= cx <= 76.1 and 18.3 <= cy <= 20.8:
            out.append(f'{it.net} PAD[{it.layer}] {it.rect}')
        continue
    pts = [it.a, it.b] if it.kind == 'trk' else [it.a]
    if all(72.9 <= p[0] <= 76.1 and 18.3 <= p[1] <= 20.8 for p in pts):
        out.append(f'{it.net} {it.kind}[{it.layer}] {it.a} {it.b if it.kind == "trk" else ""} hw{it.hw}')
txt = '\n'.join(out) + '\n'
open('/home/hatch/workspace/pdlvds-route/scratch/work/bk/bk_facts4_out.txt', 'w').write(txt)
print(txt)
print('count', len(out))
