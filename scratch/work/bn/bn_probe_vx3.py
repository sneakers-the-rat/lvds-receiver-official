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
EXTRA = {((80.875, 13.625), (81.125, 13.375)), ((81.125, 13.375), (81.375, 13.125))}
def extra_victim(it):
    if it.kind != 'trk' or it.net != 'ULPI_D4':
        return False
    a = (round(it.a[0], 3), round(it.a[1], 3)); b = (round(it.b[0], 3), round(it.b[1], 3))
    return (a, b) in EXTRA or (b, a) in EXTRA
pool = []
for it in items:
    if F3.is_victim(it) or extra_victim(it):
        continue
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if any(abs(cx - ox) < 0.01 and abs(cy - oy) < 0.01 for ox, oy in F3.C48_OLD + F3.C19_OLD):
            continue
    pool.append(it)
for net, rect in F3.C48_NEW + F3.C19_NEW:
    pool.append(G.Item(net, 'pad', layer='F.Cu', rect=rect))
BOX = (78.0, 84.0, 6.5, 17.5)
local = [it for it in pool if not (it.kind == 'trk' and (min(it.a[0], it.b[0]) > BOX[1] or max(it.a[0], it.b[0]) < BOX[0] or min(it.a[1], it.b[1]) > BOX[3] or max(it.a[1], it.b[1]) < BOX[2]))]
print(f'local pool: {len(local)}')

def solo(trks, vias):
    sc = 9.9
    for (net, layer, a, b, hw) in trks:
        for (m, d) in BG.margin_trk(a, b, layer, net, local, hw=hw):
            sc = min(sc, m)
    for (net, at) in vias:
        for (m, d) in BG.margin_via(at, net, local, r=0.25):
            sc = min(sc, m)
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

def d2(v2):
    return ([('ULPI_D2', 'F.Cu', (79.438, 13.25), (80.0, 13.12), 0.1),
             ('ULPI_D2', 'F.Cu', (80.0, 13.12), v2, 0.1),
             ('ULPI_D2', 'In2.Cu', v2, (80.05, 12.4), 0.125),
             ('ULPI_D2', 'In2.Cu', (80.05, 12.4), (80.0, 8.3), 0.125)],
            [('ULPI_D2', v2)])
def d3(vx):
    return ([('ULPI_D3', 'F.Cu', (79.95, 13.75), (79.93, 13.73), 0.1),
             ('ULPI_D3', 'In2.Cu', (79.93, 13.73), vx, 0.125),
             ('ULPI_D3', 'In2.Cu', vx, (82.2, 11.6), 0.125)],
            [('ULPI_D3', (79.93, 13.73))])
HEAD = ('ULPI_D4', 'In2.Cu', (80.46, 14.21), (81.375, 13.125), 0.125)
head_solo = solo([HEAD], [])
print(f'D4 head solo (rejoin 81.375,13.125): {head_solo:+.3f}')

res = []
for xi in range(8050, 8055):
    for yi in range(1249, 1256):
        v2 = (xi / 100, yi / 100)
        s2 = solo(*d2(v2))
        if s2 < -0.01: continue
        for xj in range(8085, 8093):
            for yj in range(1294, 1303):
                vx = (xj / 100, yj / 100)
                j = min(s2, solo(*d3(vx)), nn(d2(v2), d3(vx)),
                        nn(([HEAD], []), d3(vx)))
                res.append((j, v2, vx))
res.sort(key=lambda z: -z[0])
for j, v2, vx in res[:10]:
    print(f'joint {j:+.3f}  V2={v2}  VX={vx}')
