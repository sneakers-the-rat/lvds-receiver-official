import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
mm = lambda v: round(v/1e6, 2)
b = pcbnew.LoadBoard(sys.argv[1])
# F GND outlines as point lists; main = largest bbox area
outlines = []
for z in b.Zones():
    if z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.F_Cu):
        polys = z.GetFilledPolysList(pcbnew.F_Cu)
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            pts = [(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            outlines.append(((min(xs), max(xs), min(ys), max(ys)), pts))
outlines.sort(key=lambda t: -(t[0][1] - t[0][0]) * (t[0][3] - t[0][2]))
main = outlines[0]
print('main F outline bbox:', main[0], 'points:', len(main[1]))
def d_pt_poly(x, y, pts):
    best = 1e9
    for i in range(len(pts)):
        ax, ay = pts[i]; bx, by = pts[(i + 1) % len(pts)]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L))
        best = min(best, math.hypot(x - (ax + t * dx), y - (ay + t * dy)))
    return best
for name, (x, y) in {'X2.2 island7': (72.55, 24.57), 'C16.2 island10': (76.78, 9.75),
                     'U6.51 island12': (80.25, 4.66), 'U6.38 island13': (73.75, 4.66)}.items():
    print(f'{name}: distance pad->main F outline = {d_pt_poly(x, y, main[1]):.2f} mm')
