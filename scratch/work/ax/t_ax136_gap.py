import sys, math
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
z = None
for zz in b.Zones():
    if zz.GetNetname() == 'GND' and zz.GetLayer() == pcbnew.F_Cu:
        z = zz
        break
polys = z.GetFilledPolysList(pcbnew.F_Cu)
def outline_pts(i):
    o = polys.Outline(i)
    pts = []
    for j in range(o.PointCount()):
        p = o.CPoint(j)
        pts.append((p.x / 1e6, p.y / 1e6))
    return pts
def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))
targets = {}
for i in range(polys.OutlineCount()):
    bb = bbox(outline_pts(i))
    if abs(bb[0] - 72.68) < 0.3 and abs(bb[1] - 8.93) < 0.3:
        targets['P18'] = i
    if abs(bb[0] - 68.62) < 0.3 and abs(bb[2] - 77.79) < 0.3:
        targets['P15'] = i
    if abs(bb[0] - 75.09) < 0.3 and abs(bb[1] - 7.01) < 0.3:
        targets['P20'] = i
print('outlines found:', targets, flush=True)
def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0,
                                         ((px - ax) * dx + (py - ay) * dy)
                                         / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy)), \
        (ax + t * dx, ay + t * dy)
for other in ('P15', 'P20'):
    A = outline_pts(targets['P18'])
    Bp = outline_pts(targets[other])
    best = (9.9, None, None)
    for p in A:
        for j in range(len(Bp)):
            d, q = seg_dist(p, Bp[j], Bp[(j + 1) % len(Bp)])
            if d < best[0]:
                best = (d, p, q)
    print(f'P18 -> {other}: min dist {best[0]:.3f} at P18 pt {best[1]} '
          f'to {other} pt {best[2]}', flush=True)
