#!/usr/bin/env python3
"""bm fix3a: exp264 -> exp265. C22-move fallout + GND ties.
- C22 MOVES NE (77.05,8.9) -> (77.2,9.0): its .1 rect clears the
  ULPI_STP via (76.445,9.03) (drc264 clearance + hole_clearance).
  bm_scan3a proved the STP via has ZERO legal d0.5 sites in its
  pocket (x76.2-77.1, y8.6-10.0), so the part moves, not the via.
- ULPI_D0 F staircase re-laid whole, south + east around C22.2's
  rect (old step (77.125,8.375)->(77.375,8.625) SHORTED the pad,
  drc264 x4 + 4 mask bridges) and east of the I2C_SCL via
  (78.12,8.38); the southern jog opens the GND zone channel S of
  C22.2 (check_pcb arbitrates the island).
- PHY_1V8 hop re-laid from C22.1's new centre (77.2,9.48).
- ULPI_CK In2 dangling trim: kept column seg (76.62,17.3)->(76.62,
  13.5) has a free end at 17.3 (fix2b loop T-joins at 16.9) — re-lay
  as (76.62,16.9)->(76.62,13.5).
- GND stitch via (78.9,17.45) d0.5: bm_scan3a found exactly 2 legal
  sites in the NE pocket; EP-interior scan found 0. check_pcb
  arbitrates whether it stitches the zone<->zone pair.
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

SRC = 'hw/pdlvds_rx.exp264.kicad_pcb'
DST = 'hw/pdlvds_rx.exp265.kicad_pcb'
LAY = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}

NEW_TRK = [
    ('ULPI_D0', 'F', [(76.625, 7.875), (76.95, 7.8), (77.7, 7.75), (78.65, 7.6), (78.88, 9.15), (78.375, 9.625)], 0.25),
    ('PHY_1V8', 'F', [(77.2, 9.48), (77.6, 9.9), (77.9, 10.08)], 0.20),
    ('ULPI_CK', 'In2', [(76.62, 16.9), (76.62, 13.5)], 0.20),
]
NEW_VIA = [
    ('GND', (78.9, 17.45), 0.5),
]

RIP_BOXES = [  # (net, layer, box) — tracks with both ends in box
]
RIP_SEGS = [
    ('ULPI_D0', 'F.Cu', (76.625, 7.875), (76.875, 8.125)),
    ('ULPI_D0', 'F.Cu', (76.875, 8.125), (77.125, 8.375)),
    ('ULPI_D0', 'F.Cu', (77.125, 8.375), (77.375, 8.625)),
    ('ULPI_D0', 'F.Cu', (77.375, 8.625), (77.625, 8.875)),
    ('ULPI_D0', 'F.Cu', (77.625, 8.875), (77.875, 9.125)),
    ('ULPI_D0', 'F.Cu', (77.875, 9.125), (78.125, 9.375)),
    ('ULPI_D0', 'F.Cu', (78.125, 9.375), (78.375, 9.625)),
    ('PHY_1V8', 'F.Cu', (77.05, 9.38), (77.55, 9.85)),
    ('PHY_1V8', 'F.Cu', (77.55, 9.85), (77.9, 10.08)),
    ('ULPI_CK', 'In2.Cu', (76.62, 17.3), (76.62, 13.5)),
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
        if abs(cx - 77.05) < 0.35 and (abs(cy - 9.38) < 0.35 or abs(cy - 8.42) < 0.35):
            it.rect = (it.rect[0] + 0.15, it.rect[1] + 0.1, it.rect[2] + 0.15, it.rect[3] + 0.1)  # C22 -> (77.2, 9.0)
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
NETS = ['ULPI_D0', 'ULPI_CK', 'GND', 'PHY_1V8']
S = BL.Surgery(SRC, DST, nets=NETS)
fp = S.b.FindFootprintByReference('C22')
assert fp is not None
fp.SetPosition(pcbnew.VECTOR2I(int(77.2 * 1e6), int(9.0 * 1e6)))
print('C22 moved to (77.2, 9.0)')
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
