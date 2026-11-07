"""t_ac20: scan F-layer GND fill presence along horizontal lines.

Usage: xvfb-run -a python3 scratch/work/t_ac20_neckscan.py BOARD Y [Y...]
Prints, per Y, the x-runs (0.05 step, x 60..76) inside any F GND
filled polygon outline.
"""
import sys
import wx
_app = wx.App(False)
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.ToMM
polys = []
for z in board.Zones():
    if z.GetNetname() != 'GND' or z.GetLayer() != pcbnew.F_Cu:
        continue
    pl = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(pl.OutlineCount()):
        o = pl.Outline(i)
        pts = [(MM(o.CPoint(k).x), MM(o.CPoint(k).y))
               for k in range(o.PointCount())]
        polys.append(pts)

def pip(x, y, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xin = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xin:
                inside = not inside
    return inside

for ys in sys.argv[2:]:
    y = float(ys)
    runs = []
    cur = None
    x = 60.0
    while x <= 76.0:
        inside = any(pip(x, y, p) for p in polys)
        if inside and cur is None:
            cur = x
        if not inside and cur is not None:
            runs.append((cur, x - 0.05))
            cur = None
        x += 0.05
    if cur is not None:
        runs.append((cur, 76.0))
    print(f'y={y:+.2f}: ' + ' '.join(f'[{a:.2f},{b:.2f}]' for a, b in runs))
