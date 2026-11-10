#!/usr/bin/env python3
"""bl route2 (v2): gridroute A* for the NE braid on exp260 — PHY_1V8 pad26
stub, +3V3A pad25 feed, ULPI_D0 root — F layer only. Per-job rasters: each
net's own terminals are skipped only for its own run; ripped geometry
(fix1 stubs) is skipped globally. Strict pass uses gridroute's referee
inflation; a failed net retries at DRC-grade inflation (0.20 cap — the
board has no netclasses, KiCad's binding clearance is 0.20)."""
import json
import sys
sys.path.insert(0, 'hw')
import gridroute as gr

BOX = (76.9, 9.8, 79.6, 12.8)
ITEMS = gr.load_items('hw/pdlvds_rx.exp260.kicad_pcb')

def near(p, q, tol=0.02):
    return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol

def inb(p, box):
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]

def rect_c(it):
    r = it.rect
    return ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)

def skip_global(it):
    """Geometry ripped in fix2 regardless of routing outcome."""
    if it.net == 'PHY_1V8' and it.kind == 'trk' and it.layer == 'F' \
            and inb(it.a, (76.9, 9.9, 78.7, 11.7)) and inb(it.b, (76.9, 9.9, 78.7, 11.7)):
        return True
    if it.net == '+3V3A':
        if it.kind == 'via' and near(it.a, (78.7, 11.75)):
            return True
        if it.kind == 'trk' and it.layer == 'F' and near(it.a, (78.5, 11.562)) \
                and near(it.b, (78.7, 11.75)):
            return True
    if it.net == 'ULPI_D0' and it.kind == 'trk' and it.layer == 'F' \
            and inb(it.a, (78.8, 10.2, 79.5, 12.4)) and inb(it.b, (78.8, 10.2, 79.5, 12.4)):
        return True
    return False

def skip_own(it, net):
    if net == 'PHY_1V8':
        if it.net == 'PHY_1V8' and it.kind == 'via' and near(it.a, (77.9, 10.08)):
            return True
        if it.net == 'PHY_1V8' and it.kind == 'pad' and near(rect_c(it), (78.0, 11.562), 0.3):
            return True
    if net == '+3V3A':
        if it.net == '+3V3A' and it.kind == 'via' and near(it.a, (77.862, 10.975)):
            return True
        if it.net == '+3V3A' and it.kind == 'pad' and near(rect_c(it), (78.5, 11.562), 0.3):
            return True
    if net == 'ULPI_D0':
        if it.net == 'ULPI_D0' and it.kind == 'trk' and it.layer == 'F' \
                and (near(it.a, (78.875, 10.375)) or near(it.b, (78.875, 10.375))):
            return True
        if it.net == 'ULPI_D0' and it.kind == 'pad' and near(rect_c(it), (79.19, 12.25), 0.3):
            return True
    return False

XO_NEW = [(77.5, 11.562), (77.3, 11.02), (77.12, 10.5), (76.6, 10.45),
          (76.2, 10.0), (76.25, 9.95)]
A_NEW = [(76.5, 11.562), (76.42, 10.92), (75.95, 10.82), (75.35, 10.42),
         (74.99, 10.28)]

def build_raster(net, routed):
    r = gr.Raster(*BOX, pitch=0.05, eps=0.02)
    for it in ITEMS:
        if getattr(it, 'layer', None) == 'In1':
            continue
        if skip_global(it) or skip_own(it, net):
            continue
        r.add_item(it)
    for n2, pts in (('XO', XO_NEW), ('PHY_1V8A', A_NEW)):
        for a, b in zip(pts, pts[1:]):
            r.add_item(gr.Item(n2, 'trk', layer='F', a=a, b=b, hw=0.10))
    for n2, segs in routed:
        r.add_routed(n2, segs, [], hw=0.10)
    r.track['In2'][:] = True
    r.track['B'][:] = True
    r.via[:] = True
    return r

JOBS = [('+3V3A', (78.5, 11.562, 'F'), (77.862, 10.975, 'F')),
        ('PHY_1V8', (78.0, 11.562, 'F'), (77.9, 10.08, 'F')),
        ('ULPI_D0', (79.19, 12.25, 'F'), (78.875, 10.375, 'F'))]

orig_pair_clr = gr.pair_clr
out = {}
routed = []
for net, s, g in JOBS:
    path = None
    grade = 'strict'
    for grade, clr_cap in (('strict', None), ('drc', 0.20)):
        if clr_cap is not None:
            gr.pair_clr = lambda n, l, il, _c=clr_cap: min(orig_pair_clr(n, l, il), _c)
        r = build_raster(net, routed)
        path = gr.astar(r, s, g)
        gr.pair_clr = orig_pair_clr
        if path is not None:
            break
    if path is None:
        print(f'{net}: NO PATH (strict and drc grades)')
        out[net] = None
        continue
    segs, vias = gr.path_to_geometry(path)
    print(f'{net}: PATH grade={grade} cells={len(path)} segs={[(L, len(p)) for L, p in segs]}')
    for L, pts in segs:
        print(f'   {L}: ' + ' '.join(f'({x:.2f},{y:.2f})' for x, y in pts))
    out[net] = {'segs': segs, 'vias': vias, 'grade': grade}
    routed.append((net, [(L, a, b) for L, pts in segs for a, b in zip(pts, pts[1:])]))
json.dump(out, open('scratch/work/bl/route2.json', 'w'), indent=1)
print('wrote route2.json')
