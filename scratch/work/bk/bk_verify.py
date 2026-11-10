#!/usr/bin/env python3
"""Verify exp258: USB_RST track list vs expected; netname census of touched nets."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

items = G.load_items('/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp258.kicad_pcb')
out = []
rst = [it for it in items if it.net == 'USB_RST']
out.append(f'USB_RST items: {len(rst)}')
for it in sorted(rst, key=lambda t: (t.kind, t.layer or '', t.a, t.b or ())):
    out.append(f'  {it.kind}[{it.layer}] {it.a} {it.b if it.kind == "trk" else ""} hw{it.hw}')
exp = [
    ('F', (74.250, 16.878), (74.320, 17.550)), ('F', (74.320, 17.550), (74.450, 18.250)),
    ('In2', (74.450, 18.250), (74.300, 17.350)), ('In2', (74.300, 17.350), (74.160, 16.550)),
    ('In2', (74.160, 16.550), (74.160, 12.000)), ('In2', (74.160, 12.000), (74.140, 11.500)),
    ('In2', (74.140, 11.500), (74.130, 10.850)), ('In2', (74.130, 10.850), (74.050, 10.300)),
    ('In2', (74.050, 10.300), (74.000, 9.900)), ('In2', (74.000, 9.900), (74.140, 9.000)),
    ('In2', (74.140, 9.000), (74.140, 7.050)), ('In2', (74.140, 7.050), (74.820, 5.840)),
    ('F', (74.820, 5.840), (74.780, 5.500)), ('F', (74.780, 5.500), (74.780, 5.300)),
]
def near(p, q, tol=0.03):
    return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol
for layer, a, b in exp:
    hit = [it for it in rst if it.kind == 'trk' and it.layer == layer
           and ((near(it.a, a) and near(it.b, b)) or (near(it.a, b) and near(it.b, a)))]
    out.append(f'  expect [{layer}] {a}->{b}: {len(hit)}')
txt = '\n'.join(out) + '\n'
open('/home/hatch/workspace/pdlvds-route/scratch/work/bk/bk_verify_out.txt', 'w').write(txt)
print(txt)
