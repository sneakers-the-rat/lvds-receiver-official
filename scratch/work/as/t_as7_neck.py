"""t_as7: outline of exp236's F GND island (bbox x72.9..79.3, y-15.4..5.5),
summarized as horizontal slices: for each y in steps, the x-intervals of
the polygon interior - shows where the neck ran."""
import sys, wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.GetLayerSet().Contains(pcbnew.F_Cu):
        continue
    ps = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [(MM(o.GetPoint(j).x), MM(o.GetPoint(j).y)) for j in range(o.PointCount())]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if not (min(xs) < 73.0 and max(xs) > 79.0 and min(ys) < -15.0):
            continue
        print(f'island bbox x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}]')
        y = 5.4
        while y >= -5.0:
            ints = []
            for j in range(len(pts)):
                x1,y1 = pts[j]; x2,y2 = pts[(j+1) % len(pts)]
                if (y1 > y) != (y2 > y):
                    ints.append((x2-x1)*(y-y1)/(y2-y1)+x1)
            ints.sort()
            spans = [(round(ints[k],2), round(ints[k+1],2)) for k in range(0, len(ints)-1, 2)]
            spans = [s for s in spans if s[1]-s[0] > 0.03]
            print(f'  y={y:5.2f}: {spans}')
            y -= 0.4
print('done')
