#!/usr/bin/env python3
"""bn: exact item dump of east D-fan district on exp270."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

SRC = 'hw/pdlvds_rx.exp270.kicad_pcb'
BOX = (77.8, 8.8, 83.2, 17.8)
items = G.load_items(SRC)
out = []
for it in items:
    if it.kind == 'trk':
        cx = (it.a[0] + it.b[0]) / 2; cy = (it.a[1] + it.b[1]) / 2
        if BOX[0] <= cx <= BOX[2] and BOX[1] <= cy <= BOX[3]:
            out.append(f"trk {it.net:10s} {it.layer:3s} ({it.a[0]:.3f},{it.a[1]:.3f})->({it.b[0]:.3f},{it.b[1]:.3f}) hw={it.hw:.3f}")
    elif it.kind == 'via':
        if BOX[0] <= it.a[0] <= BOX[2] and BOX[1] <= it.a[1] <= BOX[3]:
            out.append(f"via {it.net:10s} @({it.a[0]:.3f},{it.a[1]:.3f}) r={it.hw:.3f}")
    elif it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if BOX[0] <= cx <= BOX[2] and BOX[1] <= cy <= BOX[3]:
            out.append(f"pad {it.net:10s} {it.layer:3s} rect({it.rect[0]:.3f},{it.rect[1]:.3f},{it.rect[2]:.3f},{it.rect[3]:.3f})")
out.sort()
print('\n'.join(out))
print(f'total {len(out)}')
