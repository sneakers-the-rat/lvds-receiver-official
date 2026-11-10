#!/usr/bin/env python3
"""bk facts 3: west window F + B for +3V3A via re-place along its web."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

items = G.load_items('/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb')
out = []
out.append('== window x[71.7,73.9] y[8.2,11.4]: F + B, all nets ==')
for it in items:
    if it.kind == 'pad':
        if it.layer != 'F':
            continue
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if 71.7 <= cx <= 73.9 and 8.2 <= cy <= 11.4:
            out.append(f'{it.net} PAD[F] {it.rect}')
        continue
    if it.layer not in ('F', 'B'):
        continue
    pts = [it.a, it.b] if it.kind == 'trk' else [it.a]
    if all(71.7 <= p[0] <= 73.9 and 8.2 <= p[1] <= 11.4 for p in pts):
        out.append(f'{it.net} {it.kind}[{it.layer}] {it.a} {it.b if it.kind == "trk" else ""} hw{it.hw}')
out.append('== +3V3A B horizontal pieces x[71.7,73.0] (chain y at x~72.1) ==')
for it in items:
    if it.net == '+3V3A' and it.kind == 'trk' and it.layer == 'B':
        pts = [it.a, it.b]
        if all(71.7 <= p[0] <= 73.0 for p in pts):
            out.append(f'B {it.a} {it.b} hw{it.hw}')
txt = '\n'.join(out) + '\n'
open('/home/hatch/workspace/pdlvds-route/scratch/work/bk/bk_facts3_out.txt', 'w').write(txt)
print(txt)
print('count', len(out))
