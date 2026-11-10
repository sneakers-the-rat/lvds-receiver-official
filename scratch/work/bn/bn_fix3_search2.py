"""Pair searches for the last v17 couplings: (V2 x D3-vertex), (V4), (V5 x V6)."""
import sys, itertools
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
    return sc

def nn(a_trks, a_vias, b_trks, b_vias):
    sc = 9.9
    for s1 in a_trks:
        for s2 in b_trks:
            if s1[0] != s2[0] and s1[1] == s2[1]:
                sc = min(sc, BG.seg_seg(s1[2], s1[3], s2[2], s2[3]) - s1[4] - s2[4] - 0.20)
        for (n2, at) in b_vias:
            if s1[0] != n2:
                sc = min(sc, BG.pt_seg(at, s1[2], s1[3]) - s1[4] - 0.25 - 0.20)
    for (n1, at) in a_vias:
        for s2 in b_trks:
            if n1 != s2[0]:
                sc = min(sc, BG.pt_seg(at, s2[2], s2[3]) - s2[4] - 0.25 - 0.20)
        for (n2, at2) in b_vias:
            if n1 != n2:
                d = ((at[0] - at2[0]) ** 2 + (at[1] - at2[1]) ** 2) ** 0.5
                sc = min(sc, d - 0.70)
    return sc

def d2(v2):
    return ([('ULPI_D2', 'F.Cu', (79.438, 13.25), (80.0, 13.12), 0.1),
             ('ULPI_D2', 'F.Cu', (80.0, 13.12), v2, 0.1),
             ('ULPI_D2', 'In2.Cu', v2, (79.95, 12.45), 0.125),
             ('ULPI_D2', 'In2.Cu', (79.95, 12.45), (80.0, 8.3), 0.125)],
            [('ULPI_D2', v2)])
def d3(vx):
    return ([('ULPI_D3', 'F.Cu', (79.95, 13.75), (79.93, 13.73), 0.1),
             ('ULPI_D3', 'In2.Cu', (79.93, 13.73), vx, 0.125),
             ('ULPI_D3', 'In2.Cu', vx, (82.2, 11.6), 0.125)],
            [('ULPI_D3', (79.93, 13.73))])
def d4(v4):
    return ([('ULPI_D4', 'F.Cu', (79.875, 14.375), v4, 0.1),
             ('ULPI_D4', 'In2.Cu', v4, (80.625, 13.875), 0.125)],
            [('ULPI_D4', v4)])
def d5(v5):
    return ([('ULPI_D5', 'F.Cu', (79.19, 14.75), (79.75, 14.82), 0.1),
             ('ULPI_D5', 'F.Cu', (79.75, 14.82), v5, 0.1),
             ('ULPI_D5', 'In2.Cu', v5, (80.85, 15.85), 0.125),
             ('ULPI_D5', 'In2.Cu', (80.85, 15.85), (82.0, 15.3), 0.125)],
            [('ULPI_D5', v5)])
def d6(v6):
    return ([('ULPI_D6', 'F.Cu', (81.06, 15.0), v6, 0.1),
             ('ULPI_D6', 'In2.Cu', v6, (81.375, 14.125), 0.125)],
            [('ULPI_D6', v6)])

print('--- pair A: V2 x D3vertex (also D3via vs pool in solo) ---')
d2o = []
for v2 in grid(79.9, 80.7, 12.3, 13.05, 0.05):
    t, v = d2(v2); sc = solo(t, v)
    if sc >= -0.02: d2o.append((sc, v2, t, v))
d3o = []
for vx in grid(80.55, 81.15, 12.75, 13.3, 0.05):
    t, v = d3(vx); sc = solo(t, v)
    if sc >= -0.02: d3o.append((sc, vx, t, v))
print(f'  D2 solo-ok: {len(d2o)}, D3 solo-ok: {len(d3o)}')
best = []
for s2, v2, t2, vv2 in d2o:
    for s3, vx, t3, vv3 in d3o:
        j = min(s2, s3, nn(t2, vv2, t3, vv3))
        best.append((j, v2, vx))
best.sort(key=lambda z: -z[0])
for j, v2, vx in best[:6]:
    print(f'  joint {j:+.3f}  V2={v2} VX={vx}')
# diagnose the best pair + finer grid around it
def nn_named(a_trks, a_vias, b_trks, b_vias):
    out = []
    for s1 in a_trks:
        for s2 in b_trks:
            if s1[0] != s2[0] and s1[1] == s2[1]:
                out.append((BG.seg_seg(s1[2], s1[3], s2[2], s2[3]) - s1[4] - s2[4] - 0.20,
                            f'trk {s1[0]}{s1[2]}->{s1[3]} vs trk {s2[0]}{s2[2]}->{s2[3]}'))
        for (n2, at) in b_vias:
            if s1[0] != n2:
                out.append((BG.pt_seg(at, s1[2], s1[3]) - s1[4] - 0.25 - 0.20,
                            f'trk {s1[0]}{s1[2]}->{s1[3]} vs via {n2}{at}'))
    for (n1, at) in a_vias:
        for s2 in b_trks:
            if n1 != s2[0]:
                out.append((BG.pt_seg(at, s2[2], s2[3]) - s2[4] - 0.25 - 0.20,
                            f'via {n1}{at} vs trk {s2[0]}{s2[2]}->{s2[3]}'))
        for (n2, at2) in b_vias:
            if n1 != n2:
                d = ((at[0] - at2[0]) ** 2 + (at[1] - at2[1]) ** 2) ** 0.5
                out.append((d - 0.70, f'via-via {n1}{at} {n2}{at2}'))
    return sorted(out)
print('--- pair A binder diagnosis ---')
for v2, vx in [((80.5, 12.55), (80.85, 13.0)), ((80.5, 12.55), (80.8, 13.05))]:
    t2, vv2 = d2(v2); t3, vv3 = d3(vx)
    print(f' V2={v2} solo {solo(t2, vv2):+.3f} | VX={vx} solo {solo(t3, vv3):+.3f}')
    for m, d in nn_named(t2, vv2, t3, vv3)[:3]:
        print(f'   nn {m:+.3f}  {d}')
print('--- pair A extended: leg2 join J on the kept D3 chain seg ---')
JOINS = [(82.2, 11.6), (82.45, 11.245), (82.7, 10.89)]
def d3j(vx, j):
    trks = [('ULPI_D3', 'F.Cu', (79.95, 13.75), (79.93, 13.73), 0.1),
            ('ULPI_D3', 'In2.Cu', (79.93, 13.73), vx, 0.125),
            ('ULPI_D3', 'In2.Cu', vx, j, 0.125)]
    if j != (82.2, 11.6):
        trks.append(('ULPI_D3', 'In2.Cu', j, (83.5, 9.75), 0.125))
    return trks, [('ULPI_D3', (79.93, 13.73))]
d2o = []
for v2 in grid(80.4, 80.65, 12.4, 12.7, 0.025) + [(80.54, 12.56), (80.56, 12.58), (80.58, 12.6)]:
    t, v = d2(v2); sc = solo(t, v)
    if sc >= -0.02: d2o.append((sc, v2, t, v))
d3o = []
for vx in grid(80.6, 81.25, 12.75, 13.25, 0.05):
    for j in JOINS:
        t, v = d3j(vx, j); sc = solo(t, v)
        if sc >= -0.02: d3o.append((sc, vx, j, t, v))
print(f'  ext: D2 {len(d2o)}, D3 {len(d3o)}')
fb = []
for s2, v2, t2, vv2 in d2o:
    for s3, vx, j, t3, vv3 in d3o:
        fb.append((min(s2, s3, nn(t2, vv2, t3, vv3)), v2, vx, j))
fb.sort(key=lambda z: -z[0])
for jj, v2, vx, j in fb[:8]:
    print(f'  joint {jj:+.3f}  V2={v2} VX={vx} J={j}')

print('--- pair A fine grid ---')
d2o = []
for v2 in grid(80.4, 80.6, 12.45, 12.65, 0.025):
    t, v = d2(v2); sc = solo(t, v)
    if sc >= -0.02: d2o.append((sc, v2, t, v))
d3o = []
for vx in grid(80.7, 81.0, 12.9, 13.15, 0.025):
    t, v = d3(vx); sc = solo(t, v)
    if sc >= -0.02: d3o.append((sc, vx, t, v))
print(f'  fine: D2 {len(d2o)}, D3 {len(d3o)}')
fb = []
for s2, v2, t2, vv2 in d2o:
    for s3, vx, t3, vv3 in d3o:
        fb.append((min(s2, s3, nn(t2, vv2, t3, vv3)), v2, vx))
fb.sort(key=lambda z: -z[0])
for j, v2, vx in fb[:6]:
    print(f'  joint {j:+.3f}  V2={v2} VX={vx}')

print('--- pair B: V4 vs fixed D3(pocket straight) + D6(80.85,14.8) couplings ---')
t3f, v3f = d3((80.75, 13.05))
t6f, v6f = d6((80.85, 14.8))
res = []
for v4 in grid(80.3, 80.75, 13.95, 14.45, 0.05):
    t, v = d4(v4); sc = solo(t, v)
    if sc < -0.02: continue
    j = min(sc, nn(t, v, t3f, v3f), nn(t, v, t6f, v6f))
    res.append((j, v4))
res.sort(key=lambda z: -z[0])
for j, v4 in res[:6]:
    print(f'  joint {j:+.3f}  V4={v4}')

print('--- pair C: V5 x V6 ---')
d5o = []
for v5 in grid(80.05, 80.45, 14.8, 15.15, 0.05):
    t, v = d5(v5); sc = solo(t, v)
    if sc >= -0.02: d5o.append((sc, v5, t, v))
d6o = []
for v6 in grid(80.7, 81.0, 14.6, 14.95, 0.05):
    t, v = d6(v6); sc = solo(t, v)
    if sc >= -0.02: d6o.append((sc, v6, t, v))
print(f'  D5 solo-ok: {len(d5o)}, D6 solo-ok: {len(d6o)}')
best = []
for s5, v5, t5, vv5 in d5o:
    for s6, v6, t6, vv6 in d6o:
        j = min(s5, s6, nn(t5, vv5, t6, vv6))
        best.append((j, v5, v6))
best.sort(key=lambda z: -z[0])
for j, v5, v6 in best[:6]:
    print(f'  joint {j:+.3f}  V5={v5} V6={v6}')
