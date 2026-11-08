"""Raster-diff GND F fill between two boards over a box; print the
cells filled in A but not B (the severed neck region)."""
import sys, wx
_app = wx.App(False)
import pcbnew
def fillset(path):
    b = pcbnew.LoadBoard(path)
    for z in b.Zones():
        if z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.F_Cu):
            return z.GetFilledPolysList(pcbnew.F_Cu)
    return None
pa, pb = fillset(sys.argv[1]), fillset(sys.argv[2])
x0, x1, y0, y1 = 77.0, 90.0, -19.0, -15.0
lost, gained = [], []
gy = y0
while gy <= y1:
    gx = x0
    while gx <= x1:
        v = pcbnew.VECTOR2I(pcbnew.FromMM(gx), pcbnew.FromMM(gy))
        ina, inb = pa.Contains(v), pb.Contains(v)
        if ina and not inb:
            lost.append((round(gx, 2), round(gy, 2)))
        elif inb and not ina:
            gained.append((round(gx, 2), round(gy, 2)))
        gx += 0.1
    gy += 0.1
print(f'lost {len(lost)} cells, gained {len(gained)}')
if lost:
    xs = [c[0] for c in lost]; ys = [c[1] for c in lost]
    print(f'lost bbox x[{min(xs)},{max(xs)}] y[{min(ys)},{max(ys)}]')
    rows = {}
    for (x, y) in lost:
        rows.setdefault(y, []).append(x)
    for y in sorted(rows):
        print(f'  y={y}: x {min(rows[y])}..{max(rows[y])} n={len(rows[y])}')
