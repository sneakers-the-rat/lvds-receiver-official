#!/usr/bin/env python3
"""bm fix3a2: exp266 -> exp267. GND frag19 (C22.2 moat) tie.
- ULPI_D0 southern run drops ~0.6 further south (y7.75 -> y7.15),
  widening the GND zone moat S of C22.2; GND via (77.2,7.78) d0.5
  lands in the re-flowed moat fill and ties frag19 to In1/B.
  (bm_scan_frag19: 0 legal via sites touched the moat before the
  drop; bm_frag/bm_frag2 identified frag19 as the untied fragment;
  a test via at (77.2,8.6) on a throwaway copy closed the pair.)
- Everything else from fix3a is already in exp266 — NOT repeated.
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

SRC = 'hw/pdlvds_rx.exp266.kicad_pcb'
DST = 'hw/pdlvds_rx.exp267.kicad_pcb'
LAY = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}

NEW_TRK = [
    ('ULPI_D0', 'F', [(76.375, 7.625), (76.7, 7.35), (77.45, 7.18), (78.35, 7.42), (78.62, 7.55), (78.9, 9.12), (78.375, 9.625)], 0.25),
]
NEW_VIA = [
    ('GND', (77.35, 7.84), 0.5),
]

RIP_BOXES = [  # (net, layer, box) — tracks with both ends in box
]
RIP_SEGS = [
    ('ULPI_D0', 'F.Cu', (76.375, 7.625), (76.625, 7.875)),
    ('ULPI_D0', 'F.Cu', (76.625, 7.875), (76.95, 7.8)),
    ('ULPI_D0', 'F.Cu', (76.95, 7.8), (77.7, 7.75)),
    ('ULPI_D0', 'F.Cu', (77.7, 7.75), (78.65, 7.6)),
    ('ULPI_D0', 'F.Cu', (78.65, 7.6), (78.88, 9.15)),
]
RIP_VIAS = []


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
for it in items:  # gridroute uses short layer names for pads AND tracks
    it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
pool = []
for it in items:
    if is_victim(it):
        continue
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if it.layer != 'F.Cu' and 74.3 < cx < 79.2 and 11.4 < cy < 16.6:
            continue  # U7 EP/no-net pads are F-only in reality
    pool.append(it)

bad = 0
segs = []
for net, layer, pts, w in NEW_TRK:
    for a, b in zip(pts, pts[1:]):
        segs.append((net, LAY[layer], a, b, w / 2))
for net, layer, a, b, hw in segs:
    negs = BG.report(f'{net} {layer} {a}->{b}',
                     BG.margin_trk(a, b, layer, net, pool, hw=hw), n=2)
    bad += len(negs)
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
NETS = ['ULPI_D0', 'GND']
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
