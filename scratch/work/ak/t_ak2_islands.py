"""t_ak2: summary of GND fill outlines on a layer: bbox, area-ish,
 pads (any net) whose centres fall inside, and GND pads/vias inside.
Usage: t_ak2_islands.py board LAYER"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

SRC = sys.argv[1]
LAYN = sys.argv[2]
LAY = {'F': pcbnew.F_Cu, 'In1': pcbnew.In1_Cu, 'In2': pcbnew.In2_Cu,
       'B': pcbnew.B_Cu}[LAYN]
board = pcbnew.LoadBoard(SRC)

def mm(v):
    return pcbnew.ToMM(v)

def inside(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
    return c

allpads = []
for fp in board.GetFootprints():
    for pad in fp.Pads():
        p = pad.GetPosition()
        px, py = mm(p.x), mm(p.y)
        allpads.append((f'{fp.GetReference()}.{pad.GetNumber()}',
                        pad.GetNetname(), (px, py)))
allvias = []
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        allvias.append((t.GetNetname(), (mm(p.x), mm(p.y)), mm(t.GetWidth())))

for z in board.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(LAY):
        continue
    polys = z.GetFilledPolysList(LAY)
    print(f'GND {LAYN} zone: {polys.OutlineCount()} fill outlines')
    for i in range(polys.OutlineCount()):
        ch = polys.Outline(i)
        pts = [(mm(ch.GetPoint(j).x), mm(ch.GetPoint(j).y))
               for j in range(ch.PointCount())]
        holes = []
        for h in range(polys.HoleCount(i)):
            hc = polys.Hole(i, h)
            holes.append([(mm(hc.GetPoint(j).x), mm(hc.GetPoint(j).y))
                          for j in range(hc.PointCount())])
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        def isin(pt):
            return inside(pt, pts) and not any(inside(pt, h) for h in holes)
        members = [f'{r}[{n}]' for r, n, p in allpads if isin(p)]
        gvias = [(f'{n}@({p[0]:.2f},{p[1]:.2f})d{d:.2f}')
                 for n, p, d in allvias if n == 'GND' and isin(p)]
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        print(f' outline{i}: bbox x[{min(xs):.2f},{max(xs):.2f}] '
              f'y[{min(ys):.2f},{max(ys):.2f}] bboxarea={area:.1f}')
        if members:
            print(f'    pads-in: {members}')
        if gvias:
            print(f'    gndvias-in: {gvias}')
