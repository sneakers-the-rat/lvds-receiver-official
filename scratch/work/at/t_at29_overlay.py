"""t_at29: overlay CLK-CD and DATA-DC journeys; list every mutual
conflict in exact geometry (seg-seg < 0.40 same layer, via-seg <
0.55, via-via < 0.70)."""
import json, math

def load(fn):
    d = json.load(open(fn))
    segs = []  # (layer, a, b)
    for run in d['runs']:
        pts = run['pts']
        for a, b in zip(pts, pts[1:]):
            segs.append((run['layer'], tuple(a), tuple(b)))
    return segs, [tuple(v) for v in d['vias']]

C_segs, C_vias = load('scratch/work/as/journey_CAP_CLK_CD.json')
D_segs, D_vias = load('scratch/work/as/journey_CAP_DATA_DC.json')

def pt_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0,
                    ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))

def seg_seg(a, b, c, d):
    def inter(p1, p2, p3, p4):
        def cr(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - \
                   (a[1] - o[1]) * (b[0] - o[0])
        d1, d2 = cr(p3, p4, p1), cr(p3, p4, p2)
        d3, d4 = cr(p1, p2, p3), cr(p1, p2, p4)
        return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and \
               d1 != 0 and d2 != 0 and d3 != 0 and d4 != 0
    if inter(a, b, c, d):
        return 0.0
    return min(pt_seg(a, c, d), pt_seg(b, c, d),
               pt_seg(c, a, b), pt_seg(d, a, b))

n = 0
for (l1, a, b) in C_segs:
    for (l2, c, d) in D_segs:
        if l1 != l2:
            continue
        dd = seg_seg(a, b, c, d)
        if dd < 0.395:
            print(f'SEG L{l1} CLK {a}->{b} vs DATA {c}->{d}: {dd:.3f}')
            n += 1
for v in C_vias:
    for w in D_vias:
        dd = math.hypot(v[0] - w[0], v[1] - w[1])
        if dd < 0.695:
            print(f'VIA CLK {v} vs DATA {w}: {dd:.3f}')
            n += 1
for v in C_vias:
    for (l2, c, d) in D_segs:
        dd = pt_seg(v, c, d)
        if dd < 0.545:
            print(f'VIA CLK {v} vs DATA seg L{l2} {c}->{d}: {dd:.3f}')
            n += 1
for v in D_vias:
    for (l1, a, b) in C_segs:
        dd = pt_seg(v, a, b)
        if dd < 0.545:
            print(f'VIA DATA {v} vs CLK seg L{l1} {a}->{b}: {dd:.3f}')
            n += 1
print(f'total conflicts: {n}')
print('CLK vias:', C_vias)
print('DATA vias:', D_vias)
