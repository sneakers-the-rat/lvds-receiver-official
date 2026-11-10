"""Triple search (V4,V5,V6) with V2/V3 fixed at v20 values."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bn')
import gridroute as G
import bm_gate as BG
import bn_fix3 as F3
BG.clr = lambda net: 0.20
items = G.load_items(F3.SRC)
for it in items:
    it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
pool = []
for it in items:
    if F3.is_victim(it):
        continue
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if any(abs(cx - ox) < 0.01 and abs(cy - oy) < 0.01
               for ox, oy in F3.C48_OLD + F3.C19_OLD):
            continue
    pool.append(it)
for net, rect in F3.C48_NEW + F3.C19_NEW:
    pool.append(G.Item(net, 'pad', layer='F.Cu', rect=rect))
BOX = (78.0, 84.0, 6.5, 17.5)
local = [it for it in pool if it.kind == 'via' and BOX[0] <= it.a[0] <= BOX[1] and BOX[2] <= it.a[1] <= BOX[3]]
local += [it for it in pool if it.kind == 'pad' and BOX[0] - 1 <= it.rect[0] and it.rect[2] <= BOX[1] + 1 and BOX[2] - 1 <= it.rect[1] and it.rect[3] <= BOX[3] + 1]
local += [it for it in pool if it.kind == 'trk' and BOX[0] - 1 <= min(it.a[0], it.b[0]) and max(it.a[0], it.b[0]) <= BOX[1] + 1 and BOX[2] - 1 <= min(it.a[1], it.b[1]) and max(it.a[1], it.b[1]) <= BOX[3] + 1]
print(f'local pool: {len(local)}')

FIXED = [  # v20 fixed items (D2, D3, NRST, +3V3D-feed)
    ('ULPI_D2', 'F.Cu', (79.438, 13.25), (80.0, 13.12), 0.1),
    ('ULPI_D2', 'F.Cu', (80.0, 13.12), (80.54, 12.56), 0.1),
    ('ULPI_D2', 'In2.Cu', (80.54, 12.56), (80.05, 12.4), 0.125),
    ('ULPI_D2', 'In2.Cu', (80.05, 12.4), (80.0, 8.3), 0.125),
    ('ULPI_D3', 'F.Cu', (79.95, 13.75), (79.93, 13.73), 0.1),
    ('ULPI_D3', 'In2.Cu', (79.93, 13.73), (81.22, 12.78), 0.125),
    ('ULPI_D3', 'In2.Cu', (81.22, 12.78), (82.2, 11.6), 0.125),
    ('NRST', 'F.Cu', (81.095, 11.85), (80.55, 10.65), 0.1),
    ('+3V3D', 'F.Cu', (81.12, 13.6), (81.3, 13.0), 0.1),
]
FIXED_VIA = [('ULPI_D2', (80.54, 12.56)), ('ULPI_D3', (79.93, 13.73))]

def grid(x0, x1, y0, y1, st):
    out, x = [], x0
    while x <= x1 + 1e-9:
        y = y0
        while y <= y1 + 1e-9:
            out.append((round(x, 3), round(y, 3))); y += st
        x += st
    return out

def solo(trks, vias):
    sc = 9.9
    for (net, layer, a, b, hw) in trks:
        for (m, d) in BG.margin_trk(a, b, layer, net, local, hw=hw):
            sc = min(sc, m)
    for (net, at) in vias:
        for (m, d) in BG.margin_via(at, net, local, r=0.25):
            sc = min(sc, m)
    # vs FIXED
    for (net, layer, a, b, hw) in trks:
        for (n2, l2, a2, b2, h2) in FIXED:
            if net != n2 and layer == l2:
                sc = min(sc, BG.seg_seg(a, b, a2, b2) - hw - h2 - 0.20)
        for (n2, at) in FIXED_VIA:
            if net != n2:
                sc = min(sc, BG.pt_seg(at, a, b) - hw - 0.25 - 0.20)
    for (net, at) in vias:
        for (n2, l2, a2, b2, h2) in FIXED:
            if net != n2:
                sc = min(sc, BG.pt_seg(at, a2, b2) - h2 - 0.25 - 0.20)
        for (n2, at2) in FIXED_VIA:
            if net != n2:
                sc = min(sc, ((at[0] - at2[0]) ** 2 + (at[1] - at2[1]) ** 2) ** 0.5 - 0.70)
    return sc

def nn(A, B):
    (ta, va), (tb, vb) = A, B
    sc = 9.9
    for s1 in ta:
        for s2 in tb:
            if s1[0] != s2[0] and s1[1] == s2[1]:
                sc = min(sc, BG.seg_seg(s1[2], s1[3], s2[2], s2[3]) - s1[4] - s2[4] - 0.20)
        for (n2, at) in vb:
            if s1[0] != n2:
                sc = min(sc, BG.pt_seg(at, s1[2], s1[3]) - s1[4] - 0.25 - 0.20)
    for (n1, at) in va:
        for s2 in tb:
            if n1 != s2[0]:
                sc = min(sc, BG.pt_seg(at, s2[2], s2[3]) - s2[4] - 0.25 - 0.20)
        for (n2, at2) in vb:
            if n1 != n2:
                sc = min(sc, ((at[0] - at2[0]) ** 2 + (at[1] - at2[1]) ** 2) ** 0.5 - 0.70)
    return sc

def d4(v4):
    return ([('ULPI_D4', 'F.Cu', (79.875, 14.375), v4, 0.1),
             ('ULPI_D4', 'In2.Cu', v4, (80.875, 13.625), 0.125)],
            [('ULPI_D4', v4)])
def d5(v5):
    return ([('ULPI_D5', 'F.Cu', (79.19, 14.75), (79.75, 14.82), 0.1),
             ('ULPI_D5', 'F.Cu', (79.75, 14.82), v5, 0.1),
             ('ULPI_D5', 'In2.Cu', v5, (80.85, 15.85), 0.125),
             ('ULPI_D5', 'In2.Cu', (80.85, 15.85), (82.0, 15.3), 0.125)],
            [('ULPI_D5', v5)])
def d6(v6):
    return ([('ULPI_D6', 'F.Cu', (79.438, 15.25), (79.62, 15.26), 0.1),
             ('ULPI_D6', 'F.Cu', (79.62, 15.26), (80.05, 15.5), 0.1),
             ('ULPI_D6', 'F.Cu', (80.05, 15.5), (80.3, 15.75), 0.1),
             ('ULPI_D6', 'F.Cu', (80.3, 15.75), (80.72, 15.82), 0.1),
             ('ULPI_D6', 'F.Cu', (80.72, 15.82), v6, 0.1),
             ('ULPI_D6', 'In2.Cu', v6, (81.375, 14.125), 0.125)],
            [('ULPI_D6', v6)])

o4 = [(solo(*d4(v)), v) for v in grid(80.38, 80.52, 14.13, 14.27, 0.02)]
o5 = [(solo(*d5(v)), v) for v in grid(80.03, 80.27, 14.78, 15.02, 0.02)]
o6 = [(solo(*d6(v)), v) for v in grid(80.73, 80.97, 14.63, 14.97, 0.02)]
o4 = [x for x in o4 if x[0] >= -0.02]; o5 = [x for x in o5 if x[0] >= -0.02]; o6 = [x for x in o6 if x[0] >= -0.02]
print(f'solo-ok: D4 {len(o4)}, D5 {len(o5)}, D6 {len(o6)}')
D4 = {v: (s, d4(v)) for s, v in o4}; D5 = {v: (s, d5(v)) for s, v in o5}; D6 = {v: (s, d6(v)) for s, v in o6}
res = []
for s4, v4 in o4:
    for s5, v5 in o5:
        j45 = min(s4, s5, nn(D4[v4][1], D5[v5][1]))
        if j45 < -0.02: continue
        for s6, v6 in o6:
            j = min(j45, s6, nn(D4[v4][1], D6[v6][1]), nn(D5[v5][1], D6[v6][1]))
            res.append((j, v4, v5, v6))
res.sort(key=lambda z: -z[0])
for j, v4, v5, v6 in res[:10]:
    print(f'  joint {j:+.3f}  V4={v4} V5={v5} V6={v6}')
