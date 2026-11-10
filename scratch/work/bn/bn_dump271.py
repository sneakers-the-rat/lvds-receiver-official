#!/usr/bin/env python3
"""bn dump27171: authoritative district dump via gridroute loader."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

items = G.load_items('hw/pdlvds_rx.exp271.kicad_pcb')
NETS = {'ULPI_D0', 'ULPI_D1', 'ULPI_D2', 'ULPI_D3', 'ULPI_D4', 'ULPI_D5',
        'ULPI_D6', 'ULPI_D7', 'I2C_SCL', 'NRST', '+3V3D', '+3V3A',
        'CDR_SQUELCH', 'ULPI_DIR', 'ULPI_NXT', 'ULPI_CK', 'DM_PHY', 'DP_PHY'}
out = []
for it in items:
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if 77.5 < cx < 84.5 and 8.0 < cy < 18.5:
            out.append(f'pad {it.net} [{it.layer}] rect{it.rect}')
    elif it.kind == 'via':
        if it.net in NETS and 77.5 < it.a[0] < 84.5 and 8.0 < it.a[1] < 18.5:
            out.append(f'via {it.net} @({it.a[0]:.3f},{it.a[1]:.3f}) r={it.hw}')
    else:
        mx = (it.a[0] + it.b[0]) / 2; my = (it.a[1] + it.b[1]) / 2
        if it.net in NETS and 77.5 < mx < 84.5 and 8.0 < my < 18.5:
            out.append(f'trk {it.net} [{it.layer}] ({it.a[0]:.3f},{it.a[1]:.3f})->({it.b[0]:.3f},{it.b[1]:.3f}) hw={it.hw}')
for line in sorted(out):
    print(line)
print(f'total {len(out)}')
