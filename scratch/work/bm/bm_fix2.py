#!/usr/bin/env python3
"""bm fix2: exp262 -> exp263.
North: NXT/DIR F re-lane (parallel fan), STP via -> (76.45,17.85),
CK via -> (77.48,18.05) + In2 column re-laid west at x76.0 (T-join at
(76.62,16.9) into the kept column), GND stitch via -> (78.65,18.15).
South: +3V3A redundant via (77.862,10.975) deleted + SW re-lay;
A/XI/XO/PHY parallel lanes, C22 and PHY via stay put.
Gate: exact margins vs unripped pool + new-new incl. track-via terms.
"""
import sys, math
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
import wx
_app = wx.App(False)
import pcbnew
import gridroute as G
import bm_gate as BG
import build_lib as BL

SRC = 'hw/pdlvds_rx.exp262.kicad_pcb'
DST = 'hw/pdlvds_rx.exp263.kicad_pcb'
LAY = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}

NEW_TRK = [
    ('ULPI_NXT', 'F', [(76.0, 16.438), (75.8, 17.05), (75.05, 17.25), (74.94, 17.36)], 0.20),
    ('ULPI_DIR', 'F', [(76.5, 16.438), (76.48, 17.1), (76.2, 17.35), (75.9, 17.45), (75.5, 17.8), (74.84, 18.07)], 0.20),
    ('ULPI_STP', 'F', [(77.0, 16.438), (76.92, 17.0), (76.92, 17.85), (76.74, 17.88)], 0.20),
    ('ULPI_STP', 'B', [(76.74, 17.88), (76.4, 16.3), (76.35, 14.6), (76.425, 12.9)], 0.20),
    ('ULPI_CK', 'F', [(77.5, 16.438), (77.48, 17.3), (77.48, 18.05)], 0.20),
    ('ULPI_CK', 'In2', [(77.48, 18.05), (77.3, 18.55), (76.9, 18.78), (76.5, 18.78), (76.28, 18.62), (75.9, 16.9), (76.62, 16.9)], 0.20),
    ('+3V3A', 'F', [(75.5, 11.562), (75.22, 11.1), (74.85, 10.9), (74.7, 10.76)], 0.20),
    ('PHY_1V8A', 'F', [(76.5, 11.562), (76.15, 11.15), (75.62, 10.9), (75.2, 10.52), (74.99, 10.28)], 0.20),
    ('XI', 'F', [(75.82, 10.3), (76.1, 10.75), (76.55, 11.0), (77.0, 11.562)], 0.20),
    ('XO', 'F', [(77.5, 11.562), (77.45, 11.05), (77.28, 10.82), (76.85, 10.95), (76.6, 10.5), (76.3, 10.0), (76.25, 9.95)], 0.20),
    ('PHY_1V8', 'F', [(78.0, 11.562), (78.1, 11.3), (78.05, 10.5), (77.9, 10.08)], 0.20),
]
NEW_VIA = [
    ('ULPI_STP', (76.74, 17.88), 0.5),
    ('ULPI_CK', (77.48, 18.05), 0.5),
    ('GND', (79.2, 17.35), 0.6),
]

RIP_BOXES = [  # (net, layer, box) — tracks with both ends in box
    ('ULPI_NXT', 'F.Cu', (74.8, 16.3, 76.2, 17.6)),
    ('ULPI_DIR', 'F.Cu', (74.8, 16.3, 77.2, 18.6)),
    ('ULPI_STP', 'F.Cu', (75.9, 16.3, 77.2, 18.3)),
    ('ULPI_STP', 'B.Cu', (75.9, 12.8, 77.2, 18.2)),
    ('ULPI_CK', 'F.Cu', (76.4, 16.3, 77.9, 18.2)),
    ('PHY_1V8A', 'F.Cu', (74.9, 10.2, 76.6, 11.7)),
    ('XI', 'F.Cu', (75.7, 10.2, 77.1, 11.7)),
    ('XO', 'F.Cu', (76.1, 9.8, 77.6, 11.7)),
    ('PHY_1V8', 'F.Cu', (77.85, 9.9, 78.8, 11.7)),  # excludes the kept C22 hop (77.17,10.43)->(77.9,10.08)
]
RIP_SEGS = [  # (net, layer, a, b)
    ('ULPI_CK', 'In2.Cu', (77.4, 17.85), (77.5, 18.4)),
    ('ULPI_CK', 'In2.Cu', (77.5, 18.4), (77.05, 18.8)),
    ('ULPI_CK', 'In2.Cu', (77.05, 18.8), (76.7, 18.85)),
    ('ULPI_CK', 'In2.Cu', (76.7, 18.85), (76.62, 18.3)),
    ('ULPI_CK', 'In2.Cu', (76.62, 18.3), (76.62, 17.3)),
    ('+3V3A', 'F.Cu', (75.625, 11.125), (75.875, 11.125)),
    ('+3V3A', 'F.Cu', (75.875, 11.125), (75.62, 10.78)),
    ('+3V3A', 'F.Cu', (75.62, 10.78), (74.7, 10.76)),
    ('+3V3A', 'In2.Cu', (77.862, 10.975), (76.6, 12.15)),
    ('PHY_1V8', 'F.Cu', (77.17, 10.43), (77.9, 10.08)),  # hop re-laid identically? no: kept
]
RIP_SEGS = RIP_SEGS[:-1]  # PHY hop is KEPT
RIP_VIAS = [('ULPI_STP', (76.065, 17.96)), ('ULPI_CK', (77.4, 17.85)),
            ('GND', (78.0, 18.3)), ('+3V3A', (77.862, 10.975))]


def inb(p, box):
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]


def rk(p):
    return (round(p[0], 3), round(p[1], 3))


def is_victim(it):
    n, lay = it.net, it.layer
    if it.kind == 'trk':
        a, b = rk(it.a), rk(it.b)
        for nn, ll, box in RIP_BOXES:
            if n == nn and lay == ll and inb(a, box) and inb(b, box):
                return True
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
    if it.kind == 'trk':
        it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
pool = []
for it in items:
    if is_victim(it):
        continue
    if it.kind == 'pad' and it.layer != 'F.Cu' and \
            74.3 < (it.rect[0] + it.rect[2]) / 2 < 79.2 and 11.4 < (it.rect[1] + it.rect[3]) / 2 < 16.6:
        continue  # U7 EP/no-net pads are F-only in reality
    pool.append(it)

bad = 0
segs = []
for net, layer, pts, w in NEW_TRK:
    for a, b in zip(pts, pts[1:]):
        segs.append((net, LAY[layer], a, b, w / 2))
for net, layer, a, b, hw in segs:
    bad += len(BG.report(f'{net} {layer} {a}->{b}',
                         BG.margin_trk(a, b, layer, net, pool, hw=hw), n=2))
for net, (x, y), dia in NEW_VIA:
    bad += len(BG.report(f'via {net} {(x, y)}',
                         BG.margin_via((x, y), net, pool, r=dia / 2), n=2))
for i, (n1, l1, a, b, h1) in enumerate(segs):
    for n2, l2, c, d, h2 in segs[i + 1:]:
        if n1 != n2 and l1 == l2:
            m = BG.seg_seg(a, b, c, d) - h1 - h2 - BG.clr(n2)
            if m < 0:
                bad += 1
                print(f'NN trk-trk {n1} {a}->{b} vs {n2} {c}->{d}: {m:+.3f}')
    for n2, c, dia in NEW_VIA:
        if n1 != n2:
            m = BG.pt_seg(c, a, b) - h1 - dia / 2 - BG.clr(n2)
            if m < 0:
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
NETS = ['ULPI_NXT', 'ULPI_DIR', 'ULPI_STP', 'ULPI_CK', 'GND', '+3V3A', 'PHY_1V8A', 'XI', 'XO', 'PHY_1V8']
S = BL.Surgery(SRC, DST, nets=NETS)
LAYB = {'F.Cu': BL.F, 'In2.Cu': BL.IN2, 'B.Cu': BL.B}


def find_box(net, layer, box):
    vs = S.find_tracks(net, LAYB[layer], lambda t: inb(S.ends(t)[0], box) and inb(S.ends(t)[1], box))
    print(f'find {net} {layer} {box}: {len(vs)}')
    assert vs, f'no victims {net} {layer}'
    return vs


ALLV = []
for net, layer, box in RIP_BOXES:
    ALLV += find_box(net, layer, box)
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
