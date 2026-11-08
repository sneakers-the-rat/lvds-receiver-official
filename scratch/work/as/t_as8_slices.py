"""t_as8: for every F GND island, print slices only in window x[72.5,79.5]."""
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
        if max(xs) < 72.5 or min(xs) > 79.5 or max(ys) < -5.5 or min(ys) > 6.0:
            continue
        print(f'--- island bbox x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}]')
        y = 5.4
        while y >= -5.0:
            ints = []
            for j in range(len(pts)):
                x1,y1 = pts[j]; x2,y2 = pts[(j+1) % len(pts)]
                if (y1 > y) != (y2 > y):
                    ints.append((x2-x1)*(y-y1)/(y2-y1)+x1)
            ints.sort()
            spans = [(round(ints[k],2), round(ints[k+1],2)) for k in range(0, len(ints)-1, 2)]
            spans = [s for s in spans if s[1] > 72.5 and s[0] < 79.5 and s[1]-s[0] > 0.03]
            if spans: print(f'  y={y:5.2f}: {spans}')
            y -= 0.4
print('done')
