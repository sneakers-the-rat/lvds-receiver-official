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

def d2(v2):
    return ([('ULPI_D2', 'F.Cu', (79.438, 13.25), (80.0, 13.12), 0.1),
             ('ULPI_D2', 'F.Cu', (80.0, 13.12), v2, 0.1),
             ('ULPI_D2', 'In2.Cu', v2, (79.95, 12.45), 0.125),
             ('ULPI_D2', 'In2.Cu', (79.95, 12.45), (80.0, 8.3), 0.125)],
            [('ULPI_D2', v2)])
def d3(vx, j=(82.2, 11.6)):
    trks = [('ULPI_D3', 'F.Cu', (79.95, 13.75), (79.93, 13.73), 0.1),
            ('ULPI_D3', 'In2.Cu', (79.93, 13.73), vx, 0.125),
            ('ULPI_D3', 'In2.Cu', vx, j, 0.125)]
    if j != (82.2, 11.6):
        trks.append(('ULPI_D3', 'In2.Cu', j, (83.5, 9.75), 0.125))
    return trks, [('ULPI_D3', (79.93, 13.73))]

def solo_named(trks, vias):
    out = []
    for (net, layer, a, b, hw) in trks:
        for (m, d) in BG.margin_trk(a, b, layer, net, pool, hw=hw):
            if m < 0.05: out.append((m, f'trk {net} {a}->{b} vs {d}'))
    for (net, at) in vias:
        for (m, d) in BG.margin_via(at, net, pool, r=0.25):
            if m < 0.05: out.append((m, f'via {net} {at} vs {d}'))
    return sorted(out)

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


res = []
for vx in [(x/100, y/100) for x in range(8095, 8126, 5) for y in range(1270, 1296, 5)]:
    t3, v3 = d3(vx)
    s3 = solo_named(t3, v3)
    s3min = s3[0][0] if s3 else 9.9
    t2, v2o = d2((80.54, 12.56))
    nn = nn_named(t2, v2o, t3, v3)
    nnmin = nn[0][0] if nn else 9.9
    res.append((min(s3min, nnmin), vx, s3min, nnmin))
res.sort(key=lambda z: -z[0])
for j, vx, s3, nn in res[:10]:
    print(f'joint {j:+.3f}  VX={vx}  D3solo {s3:+.3f}  nn {nn:+.3f}')
