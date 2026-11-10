#!/usr/bin/env python3
"""bn probe: legal D2 via spots + D1 corner spots in the NE pocket.
Pool = exp270 minus D1/D2 surgery victims, with C19 +0.25E, C48
+0.15S, SCL vertical x79.2 applied as replacement items."""
import sys, math
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
import gridroute as G
import bm_gate as BG

SRC = 'hw/pdlvds_rx.exp270.kicad_pcb'

RIP_SEGS = [
    ('ULPI_D1', 'F.Cu', (79.19, 12.75), (79.438, 12.75)),
    ('ULPI_D1', 'F.Cu', (79.438, 12.75), (79.93, 12.6)),
    ('ULPI_D1', 'F.Cu', (79.93, 12.6), (79.93, 11.95)),
    ('ULPI_D1', 'F.Cu', (79.93, 11.95), (79.78, 11.5)),
    ('ULPI_D1', 'F.Cu', (79.78, 11.5), (79.75, 10.9)),
    ('ULPI_D1', 'F.Cu', (79.75, 10.9), (79.35, 10.35)),
    ('ULPI_D2', 'F.Cu', (79.438, 13.25), (79.875, 13.125)),
    ('ULPI_D2', 'F.Cu', (79.875, 13.125), (80.3, 12.8)),
    ('ULPI_D2', 'In2.Cu', (80.3, 12.8), (80.0, 8.3)),
    ('I2C_SCL', 'In2.Cu', (79.45, 11.1), (79.45, 14.375)),
    ('I2C_SCL', 'In2.Cu', (79.45, 14.375), (79.0, 14.85)),
    ('NRST', 'F.Cu', (80.775, 12.0), (80.225, 10.5)),
    ('+3V3D', 'F.Cu', (80.825, 13.6), (81.55, 12.3)),
    ('+3V3D', 'F.Cu', (81.55, 12.3), (81.55, 11.05)),
    ('+3V3D', 'F.Cu', (81.55, 11.05), (81.625, 10.9)),
]
RIP_VIAS = [('ULPI_D2', (80.3, 12.8))]
OLD_RECTS = [(80.325, 11.525, 81.225, 12.475), (81.925, 11.525, 82.825, 12.475),
             (80.375, 13.125, 81.275, 14.075), (81.925, 13.125, 82.825, 14.075)]


def rk(p):
    return (round(p[0], 3), round(p[1], 3))


def is_victim(it):
    if it.kind == 'trk':
        a, b = rk(it.a), rk(it.b)
        for nn, ll, a0, b0 in RIP_SEGS:
            if it.net == nn and it.layer == ll and {a, b} == {rk(a0), rk(b0)}:
                return True
        # SCL diagonal feeding the vertical (79.15,10.6)->(79.45,11.1) also re-laid
        if it.net == 'I2C_SCL' and it.layer == 'In2.Cu' and {a, b} == {(79.15, 10.6), (79.45, 11.1)}:
            return True
    if it.kind == 'via':
        for nn, at in RIP_VIAS:
            if it.net == nn and abs(it.a[0] - at[0]) < 0.01 and abs(it.a[1] - at[1]) < 0.01:
                return True
    if it.kind == 'pad' and it.rect in OLD_RECTS:
        return True
    return False


items = G.load_items(SRC)
for it in items:
    it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
pool = []
for it in items:
    if is_victim(it):
        continue
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if it.layer != 'F.Cu' and 74.3 < cx < 79.7 and 11.4 < cy < 16.6:
            continue
    pool.append(it)
# replacement items: moved pads + moved SCL + moved NRST/+3V3D feeds
pool.append(G.Item('NRST', 'pad', layer='F.Cu', rect=(80.575, 11.525, 81.475, 12.475)))
pool.append(G.Item('GND', 'pad', layer='F.Cu', rect=(82.175, 11.525, 83.075, 12.475)))
pool.append(G.Item('+3V3D', 'pad', layer='F.Cu', rect=(80.375, 13.275, 81.275, 14.225)))
pool.append(G.Item('GND', 'pad', layer='F.Cu', rect=(81.925, 13.275, 82.825, 14.225)))
pool.append(G.Item('I2C_SCL', 'trk', layer='In2.Cu', a=(79.15, 10.6), b=(79.2, 11.1), hw=0.125))
pool.append(G.Item('I2C_SCL', 'trk', layer='In2.Cu', a=(79.2, 11.1), b=(79.2, 14.375), hw=0.125))
pool.append(G.Item('I2C_SCL', 'trk', layer='In2.Cu', a=(79.2, 14.375), b=(79.0, 14.85), hw=0.125))
pool.append(G.Item('NRST', 'trk', layer='F.Cu', a=(81.025, 12.0), b=(80.55, 10.65), hw=0.1))
pool.append(G.Item('NRST', 'trk', layer='F.Cu', a=(80.55, 10.65), b=(80.225, 10.5), hw=0.1))
pool.append(G.Item('+3V3D', 'trk', layer='F.Cu', a=(80.825, 13.75), b=(81.3, 13.0), hw=0.1))
pool.append(G.Item('+3V3D', 'trk', layer='F.Cu', a=(81.3, 13.0), b=(81.85, 12.6), hw=0.1))
pool.append(G.Item('+3V3D', 'trk', layer='F.Cu', a=(81.85, 12.6), b=(81.82, 11.0), hw=0.1))
pool.append(G.Item('+3V3D', 'trk', layer='F.Cu', a=(81.82, 11.0), b=(81.625, 10.9), hw=0.1))

print('== D2 via candidates (gate margin, worst item):')
good = []
y = 12.55
while y <= 13.30:
    x = 79.80
    while x <= 80.60:
        c = (round(x, 2), round(y, 2))
        ms = BG.margin_via(c, 'ULPI_D2', pool, r=0.25)
        w = ms[0][0] if ms else 9
        if w >= -0.05:
            good.append((w, c, ms[0][1]))
        x += 0.05
    y += 0.05
for w, c, d in sorted(good, reverse=True)[:20]:
    print(f'  via {c}: {w:+.3f} ({d})')
print(f'  total spots >= -0.05: {len(good)}')
