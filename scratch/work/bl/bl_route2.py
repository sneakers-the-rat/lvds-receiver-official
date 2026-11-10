#!/usr/bin/env python3
"""bl route2: gridroute A* for the NE braid on exp260 — PHY_1V8 pad26 stub,
+3V3A pad25 feed, ULPI_D0 root — F layer only, everything else obstacle,
including fix2's new XO connector and PHY_1V8A stub as fixed geometry.
Writes scratch/work/bl/route2.json."""
import json
import sys
sys.path.insert(0, 'hw')
import gridroute as gr

BOX = (76.9, 9.8, 79.6, 12.8)

def near(p, q, tol=0.02):
    return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol

def inb(p, box):
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]

def rect_c(it):
    r = it.rect
    return ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)

def skip(it):
    if it.net == 'PHY_1V8':
        if it.kind == 'via' and near(it.a, (77.9, 10.08)):
            return True
        if it.kind == 'trk' and it.layer == 'F' and inb(it.a, (76.9, 9.9, 78.7, 11.7)) \
                and inb(it.b, (76.9, 9.9, 78.7, 11.7)):
            return True
        if it.kind == 'pad' and near(rect_c(it), (78.0, 11.562), 0.3):
            return True
    if it.net == '+3V3A':
        if it.kind == 'via' and (near(it.a, (78.7, 11.75)) or near(it.a, (77.862, 10.975))):
            return True
        if it.kind == 'trk' and it.layer == 'F' and near(it.a, (78.5, 11.562)) \
                and near(it.b, (78.7, 11.75)):
            return True
        if it.kind == 'pad' and near(rect_c(it), (78.5, 11.562), 0.3):
            return True
    if it.net == 'ULPI_D0':
        if it.kind == 'trk' and it.layer == 'F' and inb(it.a, (78.7, 10.0, 79.5, 12.4)) \
                and inb(it.b, (78.7, 10.0, 79.5, 12.4)):
            return True
        if it.kind == 'pad' and near(rect_c(it), (79.19, 12.25), 0.3):
            return True
    return False

items = gr.load_items('hw/pdlvds_rx.exp260.kicad_pcb')
raster = gr.Raster(*BOX, pitch=0.05, eps=0.02)
n_skip = 0
for it in items:
    if getattr(it, 'layer', None) == 'In1':
        continue  # solid GND plane layer: nothing routes there
    if skip(it):
        n_skip += 1
        continue
    raster.add_item(it)
print(f'obstacles added, {n_skip} items skipped (routed nets own geometry)')
# fix2's new fixed geometry as obstacles
XO_NEW = [(77.5, 11.562), (77.3, 11.02), (77.12, 10.5), (76.6, 10.45),
          (76.2, 10.0), (76.25, 9.95)]
A_NEW = [(76.5, 11.562), (76.42, 10.92), (75.95, 10.82), (75.35, 10.42),
         (74.99, 10.28)]
for net, pts in (('XO', XO_NEW), ('PHY_1V8A', A_NEW)):
    for a, b in zip(pts, pts[1:]):
        raster.add_item(gr.Item(net, 'trk', layer='F', a=a, b=b, hw=0.10))
# F only: block other layers and all via moves
raster.track['In2'][:] = True
raster.track['B'][:] = True
raster.via[:] = True

jobs = [('+3V3A', (78.5, 11.562, 'F'), (77.862, 10.975, 'F')),
        ('PHY_1V8', (78.0, 11.562, 'F'), (77.9, 10.08, 'F')),
        ('ULPI_D0', (79.19, 12.25, 'F'), (78.875, 10.375, 'F'))]
out = {}
for net, s, g in jobs:
    path = gr.astar(raster, s, g)
    if path is None:
        print(f'{net}: NO PATH')
        out[net] = None
        continue
    segs, vias = gr.path_to_geometry(path)
    print(f'{net}: path {len(path)} cells, segs={[(L, len(p)) for L, p in segs]}, vias={vias}')
    for L, pts in segs:
        print(f'   {L}: ' + ' '.join(f'({x:.2f},{y:.2f})' for x, y in pts))
    out[net] = {'segs': [(L, pts) for L, pts in segs], 'vias': vias}
    flat = [(L, a, b) for L, pts in segs for a, b in zip(pts, pts[1:])]
    raster.add_routed(net, flat, vias, hw=0.10)
json.dump(out, open('scratch/work/bl/route2.json', 'w'), indent=1)
print('wrote route2.json')
