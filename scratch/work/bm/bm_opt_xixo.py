"""Local optimizer for the XI/XO F braid: perturb free vertices of the two
chains against bm_gate's exact margin functions (pool = exp262 minus the
fix2b victims; fixed neighbours = +3V3A lane, PHY hop, PHY chain).
Objective: maximize the minimum margin; bake the winner into bm_fix2b.py."""
import os, sys, random
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/bm')
import wx
_app = wx.App(False)
import gridroute as G
import bm_gate as BG

SRC = 'hw/pdlvds_rx.exp262.kicad_pcb'
FIXED_NEW = [  # (net, layer, pts, w) — neighbours already gate-clean, held fixed
    ('+3V3A', 'F.Cu', [(75.5, 11.562), (75.48, 11.15), (75.48, 10.86), (75.3, 10.81), (74.9, 10.83), (74.7, 10.76)], 0.20),
    ('+3V3A', 'F.Cu', [(76.0, 11.562), (75.85, 11.3), (75.49, 11.35)], 0.20),
    ('PHY_1V8', 'F.Cu', [(77.45, 10.43), (77.85, 10.3), (77.9, 10.08)], 0.20),
    ('PHY_1V8', 'F.Cu', [(78.0, 11.562), (78.0, 11.2), (77.98, 10.5), (77.9, 10.08)], 0.20),
]
RIP_BOXES = [('XI', 'F.Cu', (74.5, 9.5, 78.0, 12.0)), ('XO', 'F.Cu', (74.5, 9.5, 78.3, 12.0)),
             ('+3V3A', 'F.Cu', (74.5, 10.5, 76.3, 12.0)), ('+3V3A', 'F.Cu', (75.9, 10.8, 78.1, 11.7)),
             ('PHY_1V8', 'F.Cu', (76.8, 9.9, 78.1, 10.6))]
RIP_SEGS = [('PHY_1V8', 'F.Cu', (77.17, 10.43), (77.9, 10.08))]

def rk(p):
    return (round(p[0], 2), round(p[1], 2))

def inb(p, box):
    return box[0] - 1e-9 <= p[0] <= box[2] + 1e-9 and box[1] - 1e-9 <= p[1] <= box[3] + 1e-9

items = G.load_items(SRC)
for it in items:
    it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
pool = []
for it in items:
    if it.layer != 'F.Cu':
        continue
    if it.kind == 'pad' and 75.2 <= it.cx <= 78.3 and 12.45 <= it.cy <= 15.55:
        continue  # U7 EP F pads: tracks never legally enter the EP rect
    if it.kind == 'trk':
        a, b = rk(it.a), rk(it.b)
        if any(it.net == n and it.layer == l and inb(a, bx) and inb(b, bx) for n, l, bx in RIP_BOXES):
            continue
        if any(it.net == n and it.layer == l and {a, b} == {rk(a0), rk(b0)} for n, l, a0, b0 in RIP_SEGS):
            continue
    pool.append(it)
print('pool', len(pool))

def margins_of(net, pts, w=0.20):
    """min margin of a chain vs pool + FIXED_NEW + the other chain (passed in extra)"""
    worst = 9.9
    segs = list(zip(pts, pts[1:]))
    for it in pool:
        if it.net == net:
            continue
        for a, b in segs:
            m = BG.margin_trk(net, 'F.Cu', a, b, w, it)
            if m < worst:
                worst = m
    for n2, lay, pts2, w2 in FIXED_NEW:
        if n2 == net:
            continue
        for a, b in segs:
            for c, d in zip(pts2, pts2[1:]):
                dist = BG.seg_seg(a, b, c, d)
                m = dist - w / 2 - w2 / 2 - BG.clr(net, n2, 'F.Cu')
                if m < worst:
                    worst = m
    return worst

def pair_margin(ptsA, ptsB, w=0.20):
    worst = 9.9
    for a, b in zip(ptsA, ptsA[1:]):
        for c, d in zip(ptsB, ptsB[1:]):
            m = BG.seg_seg(a, b, c, d) - w - BG.clr('XI', 'XO', 'F.Cu')
            if m < worst:
                worst = m
    return worst

XI0 = [(75.82, 10.3), (76.1, 10.48), (76.3, 10.55), (76.55, 10.58), (76.82, 10.84), (77.0, 11.562)]
XO0 = [(77.5, 11.562), (77.36, 10.88), (77.14, 10.84), (77.02, 10.68), (76.7, 10.3), (76.5, 10.08), (76.3, 10.0)]

def score(xi, xo):
    return min(margins_of('XI', xi), margins_of('XO', xo), pair_margin(xi, xo))

best = score(XI0, XO0)
print('seed score', round(best, 3))
xi = [list(p) for p in XI0]
xo = [list(p) for p in XO0]
random.seed(42)
cur = best
for it in range(4000):
    chain = xi if random.random() < 0.5 else xo
    i = random.randrange(1, len(chain) - 1)
    dx = random.choice([-0.06, -0.04, -0.02, 0.02, 0.04, 0.06])
    dy = random.choice([-0.06, -0.04, -0.02, 0.02, 0.04, 0.06])
    old = chain[i][:]
    chain[i] = [round(old[0] + dx, 2), round(old[1] + dy, 2)]
    s = score([tuple(p) for p in xi], [tuple(p) for p in xo])
    if s >= cur:
        cur = s
        if s > best:
            best = s
            print(it, 'score', round(best, 3), 'XI', [tuple(p) for p in xi], 'XO', [tuple(p) for p in xo])
            if best >= 0.03:
                break
    else:
        chain[i] = old
print('FINAL', round(cur, 3))
print('XI =', [tuple(p) for p in xi])
print('XO =', [tuple(p) for p in xo])
