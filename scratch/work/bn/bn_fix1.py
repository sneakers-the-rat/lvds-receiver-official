#!/usr/bin/env python3
"""bn fix1 v3: exp270 -> exp271. East D-fan re-fan (bm's planned fix3d).
D0 chain frozen (+3V3A via west / D1 east); D1 middle +0.08E.
D2 via -> pocket (80.03,12.8). D3 via -> (81.6,12.8) via F thread
south of C48.1 at y13.45 then north at x81.6. D4 via stays; In2 head
re-laid east. D5 via -> (80.45,15.2). D6 via -> (80.87,14.8); fan
threads the D7-corner/D5-via saddle perpendicular to their axis.
+3V3D F feed through the x81.55 slot. Gate = bm_gate + new-vs-new."""
import sys, math
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
import wx
_app = wx.App(False)
import pcbnew
import gridroute as G
import bm_gate as BG
import build_lib as BL

SRC = 'hw/pdlvds_rx.exp270.kicad_pcb'
DST = 'hw/pdlvds_rx.exp271.kicad_pcb'
LAY = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}

NEW_TRK = [
    ('ULPI_D1', 'F', [(79.93, 12.6), (80.01, 11.95), (79.86, 11.5), (79.83, 10.9), (79.35, 10.35)], 0.2),
    ('ULPI_D2', 'F', [(79.438, 13.25), (79.72, 13.18), (80.03, 12.8)], 0.2),
    ('ULPI_D2', 'In2', [(80.03, 12.8), (80.0, 8.3)], 0.25),
    ('ULPI_D3', 'F', [(79.95, 13.75), (80.6, 13.45), (81.65, 13.45), (81.6, 12.8)], 0.2),
    ('ULPI_D3', 'In2', [(81.6, 12.8), (82.2, 11.6)], 0.25),
    ('ULPI_D4', 'In2', [(80.2, 14.45), (80.5, 14.2), (80.75, 13.95), (80.875, 13.625)], 0.25),
    ('ULPI_D5', 'F', [(79.19, 14.75), (79.7, 14.8), (80.45, 15.2)], 0.2),
    ('ULPI_D5', 'In2', [(80.45, 15.2), (80.8, 15.55), (81.3, 15.35)], 0.2),
    ('ULPI_D6', 'F', [(79.438, 15.25), (79.73, 15.18), (80.05, 15.8), (80.5, 16.0), (81.15, 15.35), (80.87, 14.8)], 0.2),
    ('ULPI_D6', 'In2', [(80.87, 14.8), (81.375, 14.125)], 0.2),
    ('+3V3D', 'F', [(80.825, 13.6), (81.25, 12.95), (81.55, 12.55), (81.55, 11.0), (81.625, 10.9)], 0.2),
]
NEW_VIA = [
    ('ULPI_D2', (80.03, 12.8), 0.5),
    ('ULPI_D3', (81.6, 12.8), 0.5),
    ('ULPI_D5', (80.45, 15.2), 0.5),
    ('ULPI_D6', (80.87, 14.8), 0.5),
]

RIP_SEGS = [
    ('ULPI_D1', 'F.Cu', (79.93, 12.6), (79.93, 11.95)),
    ('ULPI_D1', 'F.Cu', (79.93, 11.95), (79.78, 11.5)),
    ('ULPI_D1', 'F.Cu', (79.78, 11.5), (79.75, 10.9)),
    ('ULPI_D1', 'F.Cu', (79.75, 10.9), (79.35, 10.35)),
    ('ULPI_D2', 'F.Cu', (79.438, 13.25), (79.875, 13.125)),
    ('ULPI_D2', 'F.Cu', (79.875, 13.125), (80.3, 12.8)),
    ('ULPI_D2', 'In2.Cu', (80.3, 12.8), (80.0, 8.3)),
    ('ULPI_D3', 'F.Cu', (79.95, 13.75), (80.15, 13.7)),
    ('ULPI_D3', 'In2.Cu', (80.15, 13.7), (82.2, 11.6)),
    ('ULPI_D4', 'In2.Cu', (80.2, 14.45), (80.375, 14.125)),
    ('ULPI_D4', 'In2.Cu', (80.375, 14.125), (80.625, 13.875)),
    ('ULPI_D5', 'F.Cu', (79.19, 14.75), (79.75, 14.78)),
    ('ULPI_D5', 'F.Cu', (79.75, 14.78), (80.15, 15.05)),
    ('ULPI_D5', 'F.Cu', (80.15, 15.05), (80.35, 15.14)),
    ('ULPI_D5', 'F.Cu', (80.35, 15.14), (80.25, 15.188)),
    ('ULPI_D5', 'In2.Cu', (80.25, 15.188), (81.3, 15.35)),
    ('ULPI_D6', 'F.Cu', (79.438, 15.25), (79.875, 15.375)),
    ('ULPI_D6', 'F.Cu', (79.875, 15.375), (80.125, 15.625)),
    ('ULPI_D6', 'F.Cu', (80.125, 15.625), (80.625, 15.625)),
    ('ULPI_D6', 'F.Cu', (80.625, 15.625), (80.0, 15.75)),
    ('ULPI_D6', 'F.Cu', (80.0, 15.75), (80.875, 15.75)),
    ('ULPI_D6', 'F.Cu', (80.875, 15.75), (81.0, 14.4)),
    ('ULPI_D6', 'In2.Cu', (81.0, 14.4), (81.375, 14.125)),
    ('+3V3D', 'F.Cu', (80.825, 13.6), (81.55, 12.3)),
    ('+3V3D', 'F.Cu', (81.55, 12.3), (81.55, 11.05)),
    ('+3V3D', 'F.Cu', (81.55, 11.05), (81.625, 10.9)),
]
RIP_VIAS = [
    ('ULPI_D2', (80.3, 12.8)),
    ('ULPI_D3', (80.15, 13.7)),
    ('ULPI_D5', (80.25, 15.188)),
    ('ULPI_D6', (81.0, 14.4)),
]


def rk(p):
    return (round(p[0], 3), round(p[1], 3))


def is_victim(it):
    n, lay = it.net, it.layer
    if it.kind == 'trk':
        a, b = rk(it.a), rk(it.b)
        for nn, ll, a0, b0 in RIP_SEGS:
            if n == nn and lay == ll and {a, b} == {rk(a0), rk(b0)}:
                return True
    if it.kind == 'via':
        for nn, at in RIP_VIAS:
            if n == nn and abs(it.a[0] - at[0]) < 0.01 and abs(it.a[1] - at[1]) < 0.01:
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


def allowed(subj, desc, m):
    # Declared exception class (bm precedent): gate prices power pads
    # at 0.25 where KiCad's binding rule is 0.20. A margin >= -0.05
    # against a POWER pad rect is KiCad-legal (>= 0.00). Nothing else.
    return m >= -0.05 and 'pad' in desc and ('+3V3D' in desc or '+3V3A' in desc)


bad = 0
segs = []
for net, layer, pts, w in NEW_TRK:
    for a, b in zip(pts, pts[1:]):
        segs.append((net, LAY[layer], a, b, w / 2))
for net, layer, a, b, hw in segs:
    negs = BG.report(f'{net} {layer} {a}->{b}',
                     BG.margin_trk(a, b, layer, net, pool, hw=hw), n=2)
    bad += len([1 for (m, d) in negs if not allowed(net, d, m)])
for net, (x, y), dia in NEW_VIA:
    negs = BG.report(f'via {net} {(x, y)}',
                     BG.margin_via((x, y), net, pool, r=dia / 2), n=2)
    bad += len([1 for (m, d) in negs if not allowed(net, d, m)])
for i, (n1, l1, a, b, h1) in enumerate(segs):
    for n2, l2, c, d, h2 in segs[i + 1:]:
        if n1 != n2 and l1 == l2:
            m = BG.seg_seg(a, b, c, d) - h1 - h2 - BG.clr(n2)
            if m < 0 and not allowed(n1, f'vs {n2}', m):
                bad += 1
                print(f'NN trk-trk {n1} {a}->{b} vs {n2} {c}->{d}: {m:+.3f}')
    for n2, c, dia in NEW_VIA:
        if n1 != n2:
            m = BG.pt_seg(c, a, b) - h1 - dia / 2 - BG.clr(n2)
            if m < 0 and not allowed(n1, f'vs via {n2}', m):
                bad += 1
                print(f'NN trk-via {n1} {a}->{b} vs via {n2}@{c}: {m:+.3f}')
for i, (n1, c1, d1) in enumerate(NEW_VIA):
    for n2, c2, d2 in NEW_VIA[i + 1:]:
        if n1 != n2:
            m = math.hypot(c1[0] - c2[0], c1[1] - c2[1]) - d1 / 2 - d2 / 2 - BG.clr(n2)
            if m < 0:
                bad += 1
                print(f'NN via-via {n1}@{c1} vs {n2}@{c2}: {m:+.3f}')
print('gate negatives:', bad)
if bad:
    print('GATE FAILED — not building')
    sys.exit(1)
print('gate clean; building')

# ---------------- build ----------------
NETS = ['ULPI_D1', 'ULPI_D2', 'ULPI_D3', 'ULPI_D4', 'ULPI_D5', 'ULPI_D6', '+3V3D']
S = BL.Surgery(SRC, DST, nets=NETS)
LAYB = {'F.Cu': BL.F, 'In2.Cu': BL.IN2, 'B.Cu': BL.B}

ALLV = []
for net, layer, a, b in RIP_SEGS:
    ALLV += S.find_seg(net, LAYB[layer], a, b)
for net, at in RIP_VIAS:
    ALLV += S.find_via(net, at)
S.remove(ALLV)

for net, layer, pts, w in NEW_TRK:
    S.add_polyline(net, LAYB[LAY[layer]], pts, w)
for net, (x, y), dia in NEW_VIA:
    S.add_via(net, x, y, dia=dia, drill=0.3)
S.finish()
