"""Scan a GND F fill outline (selected by bbox) for a d0.5 via point
gating F/In2/B in the exact item model (t_ai_lib)."""
import sys, wx
_app = wx.App(False)
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/work/ai')
import pcbnew
from t_ai_lib import load_items, pt_margin, in_box_pool

b = pcbnew.LoadBoard(sys.argv[1])
poly_pts = None
for z in b.Zones():
    if z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.F_Cu):
        polys = z.GetFilledPolysList(pcbnew.F_Cu)
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            pts = [(pcbnew.ToMM(o.GetPoint(j).x), pcbnew.ToMM(o.GetPoint(j).y))
                   for j in range(o.PointCount())]
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            if abs(min(xs) - 78.08) < 0.1 and abs(max(ys) + 15.83) < 0.1:
                poly_pts = pts
                print(f'pocket outline{i}: bbox x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}] npts={len(pts)}')
assert poly_pts, 'pocket outline not found'

def inside(x, y):
    n = len(poly_pts); c = False
    for i in range(n):
        x1, y1 = poly_pts[i]; x2, y2 = poly_pts[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                c = not c
    return c

items = load_items(b)
xs = [p[0] for p in poly_pts]; ys = [p[1] for p in poly_pts]
pool = in_box_pool(items, (min(xs), max(xs), min(ys), max(ys)), pad=1.2)
best = []
gx = min(xs) + 0.3
while gx < max(xs) - 0.2:
    gy = min(ys) + 0.3
    while gy < max(ys) - 0.2:
        if inside(gx, gy):
            ms = [pt_margin(li, gx, gy, 'GND', 0.25, pool[li])[0] for li in range(3)]
            best.append((min(ms), gx, gy, ms))
        gy += 0.125
    gx += 0.125
best.sort(reverse=True)
print(f'{len(best)} in-polygon points; top 10:')
for m, x, y, ms in best[:10]:
    print(f'  ({x:.3f},{y:.3f}) min {m:+.3f}  F {ms[0]:+.3f} In2 {ms[1]:+.3f} B {ms[2]:+.3f}')
