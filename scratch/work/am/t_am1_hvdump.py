"""HV pocket dump on exp231: all copper in x[19,40] y[-11,5]."""
import sys, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.ToMM
LAY = {0: 'F', 2: 'In2', 31: 'B'}
def inbox(x, y):
    return 19 <= x <= 40 and -11 <= y <= 5
print('--- PADS ---')
for fp in b.GetFootprints():
    fx, fy = MM(fp.GetPosition().x), MM(fp.GetPosition().y)
    if not inbox(fx, fy):
        continue
    for pad in fp.Pads():
        x, y = MM(pad.GetPosition()); sx, sy = MM(pad.GetSize())
        layers = ''.join(n for (li, n) in LAY.items() if pad.IsOnLayer(li))
        print(f'PAD {fp.GetReference()}.{pad.GetPadName()} {pad.GetNetname()} ({x:.3f},{y:.3f}) {sx:.2f}x{sy:.2f} rot{pad.GetOrientationDegrees():.0f} L{layers}')
print('--- TRACKS/VIAS ---')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = MM(t.GetPosition())
        if inbox(x, y):
            print(f'VIA {t.GetNetname()} ({x:.3f},{y:.3f}) d{MM(t.GetWidth()):.2f} drill{MM(t.GetDrillValue()):.2f}')
    else:
        a = MM(t.GetStart()); c = MM(t.GetEnd())
        if inbox(*a) or inbox(*c):
            print(f'SEG {t.GetNetname()} {LAY.get(t.GetLayer(), t.GetLayer())} ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
print('--- GND zone F fill outlines touching box ---')
for z in b.Zones():
    if z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.F_Cu):
        polys = z.GetFilledPolysList(pcbnew.F_Cu)
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            xs = [MM(o.CPoint(j).x) for j in range(o.PointCount())]
            ys = [MM(o.CPoint(j).y) for j in range(o.PointCount())]
            if xs and max(xs) > 19 and min(xs) < 40 and max(ys) > -11 and min(ys) < 5:
                print(f'  outline{i} bbox x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}] pts{o.PointCount()}')
