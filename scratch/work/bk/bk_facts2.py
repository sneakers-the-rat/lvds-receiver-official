#!/usr/bin/env python3
"""bk facts 2: CK/PHY In2 topology near the jog; XO F full; window F+In2 east."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

items = G.load_items('/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb')
out = []
out.append('== ULPI_CK + PHY_1V8A items, x[73.8,76.2] y[5.5,12.5], all layers ==')
for it in sorted(items, key=lambda t: (t.net, t.kind, t.layer or '')):
    if it.net not in ('ULPI_CK', 'PHY_1V8A'):
        continue
    pts = [it.a, it.b] if it.kind == 'trk' else [it.a]
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if 73.8 <= cx <= 76.2 and 5.5 <= cy <= 12.5:
            out.append(f'{it.net} PAD[{it.layer}] {it.rect}')
        continue
    if all(73.8 <= p[0] <= 76.2 and 5.5 <= p[1] <= 12.5 for p in pts):
        out.append(f'{it.net} {it.kind}[{it.layer}] {it.a} {it.b if it.kind == "trk" else ""} hw{it.hw}')
out.append('== XO all F items board-wide ==')
for it in items:
    if it.net == 'XO' and it.layer == 'F':
        out.append(f'XO {it.kind} {it.a} {it.b if it.kind == "trk" else ""} hw{it.hw}')
out.append('== window x[74.0,77.3] y[8.2,11.4]: F + In2, all nets ==')
for it in items:
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if 74.0 <= cx <= 77.3 and 8.2 <= cy <= 11.4:
            out.append(f'{it.net} PAD[{it.layer}] {it.rect}')
        continue
    if it.layer not in ('F', 'In2'):
        continue
    pts = [it.a, it.b] if it.kind == 'trk' else [it.a]
    if all(74.0 <= p[0] <= 77.3 and 8.2 <= p[1] <= 11.4 for p in pts):
        out.append(f'{it.net} {it.kind}[{it.layer}] {it.a} {it.b if it.kind == "trk" else ""} hw{it.hw}')
txt = '\n'.join(out) + '\n'
open('/home/hatch/workspace/pdlvds-route/scratch/work/bk/bk_facts2_out.txt', 'w').write(txt)
print(txt)
print('count', len(out))
