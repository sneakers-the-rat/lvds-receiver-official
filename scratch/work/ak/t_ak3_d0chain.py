"""t_ak3: full track chains for named nets + which F GND fill
outline contains given probe points. Usage:
  t_ak3_d0chain.py board NET [NET...] -- probes x,y ..."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

SRC = sys.argv[1]
args = sys.argv[2:]
if '--' in args:
    k = args.index('--')
    nets, probes = args[:k], args[k + 1:]
else:
    nets, probes = args, []
board = pcbnew.LoadBoard(SRC)

def mm(v):
    return pcbnew.ToMM(v)

LAYN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
        pcbnew.B_Cu: 'B'}
for t in board.GetTracks():
    if t.GetNetname() not in nets:
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        pv = t.GetPosition()
        print(f'  VIA [{t.GetNetname()}] ({mm(pv.x):.3f},{mm(pv.y):.3f}) '
              f'd{mm(t.GetWidth()):.2f}')
    else:
        a = (mm(t.GetStart().x), mm(t.GetStart().y))
        b = (mm(t.GetEnd().x), mm(t.GetEnd().y))
        print(f'  SEG {LAYN.get(t.GetLayer(), t.GetLayer())} '
              f'[{t.GetNetname()}] ({a[0]:.3f},{a[1]:.3f})->'
              f'({b[0]:.3f},{b[1]:.3f}) w{mm(t.GetWidth()):.2f}')
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() in nets:
            pv = pad.GetPosition()
            print(f'  PAD {fp.GetReference()}.{pad.GetNumber()} '
                  f'[{pad.GetNetname()}] ({mm(pv.x):.3f},{mm(pv.y):.3f})')

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

if probes:
    pts = [tuple(map(float, p.split(','))) for p in probes]
    for z in board.Zones():
        if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu):
            continue
        polys = z.GetFilledPolysList(pcbnew.F_Cu)
        for i in range(polys.OutlineCount()):
            ch = polys.Outline(i)
            poly = [(mm(ch.GetPoint(j).x), mm(ch.GetPoint(j).y))
                    for j in range(ch.PointCount())]
            holes = []
            for h in range(polys.HoleCount(i)):
                hc = polys.Hole(i, h)
                holes.append([(mm(hc.GetPoint(j).x), mm(hc.GetPoint(j).y))
                              for j in range(hc.PointCount())])
            for pt in pts:
                if inside(pt, poly) and not any(inside(pt, h)
                                                for h in holes):
                    print(f'  probe {pt} -> outline{i}')
