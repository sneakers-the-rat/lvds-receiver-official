"""Diff GND F fill outlines between two boards: count + bboxes."""
import sys, wx
_app = wx.App(False)
import pcbnew
def outlines(path):
    b = pcbnew.LoadBoard(path)
    gvias = [(pcbnew.ToMM(t.GetPosition())[0], pcbnew.ToMM(t.GetPosition())[1])
             for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == 'GND']
    out = []
    for z in b.Zones():
        if z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.F_Cu):
            polys = z.GetFilledPolysList(pcbnew.F_Cu)
            for i in range(polys.OutlineCount()):
                o = polys.Outline(i)
                pts = [(pcbnew.ToMM(o.GetPoint(j).x), pcbnew.ToMM(o.GetPoint(j).y))
                       for j in range(o.PointCount())]
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                nv = sum(1 for (vx, vy) in gvias if min(xs) <= vx <= max(xs) and min(ys) <= vy <= max(ys))
                out.append((round(min(xs),2), round(max(xs),2), round(min(ys),2), round(max(ys),2), len(pts), nv))
    return sorted(out)
a = outlines(sys.argv[1]); c = outlines(sys.argv[2])
print(f'{sys.argv[1]}: {len(a)} outlines; {sys.argv[2]}: {len(c)}')
for x in a:
    if x not in c: print('  only-A', x)
for x in c:
    if x not in a: print('  only-B', x)
