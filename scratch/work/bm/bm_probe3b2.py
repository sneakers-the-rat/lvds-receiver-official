#!/usr/bin/env python3
"""Scan A-chain bend points against the real exp267 pool (gate-exact)."""
import sys, itertools
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
import wx
_app = wx.App(False)
import gridroute as G
import bm_gate as BG

SRC = 'hw/pdlvds_rx.exp267.kicad_pcb'
RIP_SEGS = [
    ('XI', 'F.Cu', (75.82, 10.3), (76.2, 10.42)),
    ('XI', 'F.Cu', (76.2, 10.42), (76.48, 10.5)),
    ('XI', 'F.Cu', (76.48, 10.5), (76.78, 10.6)),
    ('XI', 'B.Cu', (75.32, 12.75), (75.82, 10.3)),
    ('PHY_1V8A', 'F.Cu', (76.5, 11.562), (76.42, 10.92)),
    ('PHY_1V8A', 'F.Cu', (76.42, 10.92), (75.95, 10.82)),
    ('PHY_1V8A', 'F.Cu', (75.95, 10.82), (75.35, 10.42)),
    ('PHY_1V8A', 'F.Cu', (75.35, 10.42), (74.99, 10.28)),
    ('PHY_1V8A', 'B.Cu', (74.99, 10.28), (75.0, 11.5)),
    ('PHY_1V8A', 'B.Cu', (75.0, 11.5), (74.45, 12.1)),
    ('+3V3A', 'F.Cu', (75.875, 11.125), (75.62, 10.78)),
    ('+3V3A', 'F.Cu', (75.62, 10.78), (74.7, 10.76)),
    ('+3V3A', 'F.Cu', (74.7, 10.76), (74.375, 10.625)),
    ('+3V3A', 'F.Cu', (74.375, 10.625), (73.625, 10.625)),
]
XI_NEW = [((75.82, 10.3), (76.1, 10.25)), ((76.1, 10.25), (76.28, 10.42)),
          ((76.28, 10.42), (76.53, 10.49)), ((76.53, 10.49), (76.78, 10.6))]

def rk(p):
    return (round(p[0], 3), round(p[1], 3))

items = G.load_items(SRC)
for it in items:
    it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
pool = []
for it in items:
    if it.kind == 'trk' and any(it.net == n and it.layer == l and {rk(it.a), rk(it.b)} == {rk(a), rk(b)} for (n, l, a, b) in RIP_SEGS):
        continue
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if it.layer != 'F.Cu' and 74.3 < cx < 79.2 and 11.4 < cy < 16.6:
            continue
    pool.append(it)

def chain_margins(pts):
    out = []
    for a, b in zip(pts, pts[1:]):
        ms = BG.margin_trk(a, b, 'F.Cu', 'PHY_1V8A', pool, hw=0.1)
        out += [(m, d, a, b) for (m, d) in ms if m < 0.02]
        for (c, d) in XI_NEW:
            m = BG.seg_seg(a, b, c, d) - 0.2 - BG.clr('XI')
            if m < 0.02:
                out.append((m, f'NN XI {c}->{d}', a, b))
    return sorted(out)

best = []
for ys1 in (10.88, 10.9):
    for y1 in (10.78, 10.8):
        for y2 in (10.66, 10.68):
            for y3 in (10.62, 10.64):
                pts = [(76.5, 11.562), (76.45, ys1), (76.22, y1), (75.93, y2), (75.65, y3), (75.5, 10.52), (75.2, 10.35), (74.99, 10.28)]
                ms = chain_margins(pts)
                # score: worst margin excluding PV-via (exception) and pad30 (exception)
                hard = [m for (m, d, a, b) in ms if 'via XI' not in d and 'pad +3V3A' not in d]
                best.append((min(hard) if hard else 9, ys1, y1, y2, y3, pts))
best.sort(key=lambda t: -t[0])
for s, ys1, y1, y2, y3, pts in best[:5]:
    print(f'ys1={ys1} y1={y1} y2={y2} y3={y3}: worst-hard {s:+.3f}')
s, ys1, y1, y2, y3, pts = best[0]
print('best chain full low margins:')
for m, d, a, b in chain_margins(pts):
    print(f'  {m:+.3f} {d}  on {a}->{b}')
