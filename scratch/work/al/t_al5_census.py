"""Reload census + GND island test for a board file."""
import sys, wx
_app = wx.App(False)
import pcbnew
from collections import Counter
b = pcbnew.LoadBoard(sys.argv[1])
c = Counter()
for t in b.GetTracks():
    c[t.GetNetname()] += 1
print('census: +3V3D items', c['+3V3D'], '| GND items', c['GND'], '| total', sum(c.values()))
for z in b.Zones():
    if z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.F_Cu):
        polys = z.GetFilledPolysList(pcbnew.F_Cu)
        print('GND F fill outlines:', polys.OutlineCount())
        gvias = [(pcbnew.ToMM(t.GetPosition())[0], pcbnew.ToMM(t.GetPosition())[1])
                 for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == 'GND']
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            pts = [(pcbnew.ToMM(o.GetPoint(j).x), pcbnew.ToMM(o.GetPoint(j).y))
                   for j in range(o.PointCount())]
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            if min(xs) < 73.75 < max(xs) and min(ys) < 4.662 < max(ys):
                nv = sum(1 for (vx, vy) in gvias if min(xs) <= vx <= max(xs) and min(ys) <= vy <= max(ys))
                print(f'  outline{i} holds U6.38: bbox x[{min(xs):.3f},{max(xs):.3f}] y[{min(ys):.3f},{max(ys):.3f}] gnd_vias_in_bbox={nv}')
