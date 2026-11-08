"""t_al1: full dump of the U6 north-mouth district on a board.
Usage: t_al1_dump.py board x0 x1 y0 y1 [net ...]
Prints pads (with size/rot), tracks, vias whose geometry intersects
the box (bounding-circle test for pads/vias), full chains of the
named nets anywhere, and GND F fill outlines intersecting the box."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

SRC = sys.argv[1]
X0, X1, Y0, Y1 = map(float, sys.argv[2:6])
NETS = sys.argv[6:]
board = pcbnew.LoadBoard(SRC)

def mm(v):
    return pcbnew.ToMM(v)

LAYN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
        pcbnew.B_Cu: 'B'}

print('--- pads in box ---')
for fp in board.GetFootprints():
    for pad in fp.Pads():
        pv = pad.GetPosition()
        p = (mm(pv.x), mm(pv.y))
        sx, sy = pcbnew.ToMM(pad.GetSize())
        import math
        reach = math.hypot(sx, sy) / 2
        if p[0] + reach < X0 or p[0] - reach > X1 or \
           p[1] + reach < Y0 or p[1] - reach > Y1:
            continue
        print(f'  {fp.GetReference()}.{pad.GetNumber()} '
              f'[{pad.GetNetname()}] ({p[0]:.3f},{p[1]:.3f}) '
              f'{sx:.3f}x{sy:.3f} rot{pad.GetOrientationDegrees():.0f} '
              f'layers={"".join(LAYN.get(l, "?") for l in [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu] if pad.IsOnLayer(l))}')

print('--- tracks/vias touching box ---')
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        pv = t.GetPosition()
        p = (mm(pv.x), mm(pv.y))
        r = mm(t.GetWidth()) / 2
        if p[0] + r < X0 or p[0] - r > X1 or p[1] + r < Y0 or p[1] - r > Y1:
            continue
        print(f'  VIA [{t.GetNetname()}] ({p[0]:.3f},{p[1]:.3f}) '
              f'd{mm(t.GetWidth()):.2f} drill{mm(t.GetDrillValue()):.2f}')
    else:
        a = (mm(t.GetStart().x), mm(t.GetStart().y))
        b = (mm(t.GetEnd().x), mm(t.GetEnd().y))
        if max(a[0], b[0]) < X0 or min(a[0], b[0]) > X1 or \
           max(a[1], b[1]) < Y0 or min(a[1], b[1]) > Y1:
            continue
        print(f'  SEG {LAYN.get(t.GetLayer(), t.GetLayer())} '
              f'[{t.GetNetname()}] ({a[0]:.3f},{a[1]:.3f})->'
              f'({b[0]:.3f},{b[1]:.3f}) w{mm(t.GetWidth()):.2f}')

if NETS:
    print('--- full chains ---')
    for t in board.GetTracks():
        if t.GetNetname() not in NETS:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            pv = t.GetPosition()
            print(f'  VIA [{t.GetNetname()}] ({mm(pv.x):.3f},'
                  f'{mm(pv.y):.3f}) d{mm(t.GetWidth()):.2f}')
        else:
            a = (mm(t.GetStart().x), mm(t.GetStart().y))
            b = (mm(t.GetEnd().x), mm(t.GetEnd().y))
            print(f'  SEG {LAYN.get(t.GetLayer(), t.GetLayer())} '
                  f'[{t.GetNetname()}] ({a[0]:.3f},{a[1]:.3f})->'
                  f'({b[0]:.3f},{b[1]:.3f}) w{mm(t.GetWidth()):.2f}')
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() in NETS:
                pv = pad.GetPosition()
                print(f'  PAD {fp.GetReference()}.{pad.GetNumber()} '
                      f'[{pad.GetNetname()}] ({mm(pv.x):.3f},'
                      f'{mm(pv.y):.3f})')

print('--- GND F fill outlines in box ---')
for z in board.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu):
        continue
    polys = z.GetFilledPolysList(pcbnew.F_Cu)
    print(f'GND F zone: {polys.OutlineCount()} fill outlines')
    for i in range(polys.OutlineCount()):
        ch = polys.Outline(i)
        pts = [(mm(ch.GetPoint(j).x), mm(ch.GetPoint(j).y))
               for j in range(ch.PointCount())]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) < X0 or min(xs) > X1 or max(ys) < Y0 or min(ys) > Y1:
            continue
        nv = 0
        for t in board.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == 'GND':
                pv = t.GetPosition()
                p = (mm(pv.x), mm(pv.y))
                if min(xs) - 0.01 <= p[0] <= max(xs) + 0.01 and \
                   min(ys) - 0.01 <= p[1] <= max(ys) + 0.01:
                    nv += 1
        print(f' outline{i}: bbox x[{min(xs):.3f},{max(xs):.3f}] '
              f'y[{min(ys):.3f},{max(ys):.3f}] npts={len(pts)} '
              f'gnd_vias_in_bbox={nv}')
