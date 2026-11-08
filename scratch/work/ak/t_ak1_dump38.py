"""t_ak1: dump GND F.Cu fill islands and all copper items around U6.38.
Usage: t_ak1_dump38.py board x0 x1 y0 y1"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

SRC = sys.argv[1]
X0, X1, Y0, Y1 = map(float, sys.argv[2:6])
board = pcbnew.LoadBoard(SRC)

def mm(v):
    return pcbnew.ToMM(v)

# --- fill islands on F for GND zones
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
        print(f' outline{i}: bbox x[{min(xs):.3f},{max(xs):.3f}] '
              f'y[{min(ys):.3f},{max(ys):.3f}] npts={len(pts)}')
        for p in pts:
            print(f'    ({p[0]:.3f},{p[1]:.3f})')
        for h in range(polys.HoleCount(i)):
            hc = polys.Hole(i, h)
            hpts = [(mm(hc.GetPoint(j).x), mm(hc.GetPoint(j).y))
                    for j in range(hc.PointCount())]
            print(f'  hole{h}: {len(hpts)} pts '
                  f'bbox x[{min(q[0] for q in hpts):.3f},'
                  f'{max(q[0] for q in hpts):.3f}] '
                  f'y[{min(q[1] for q in hpts):.3f},'
                  f'{max(q[1] for q in hpts):.3f}]')

def inbox(x, y, pad=2.0):
    return X0 - pad <= x <= X1 + pad and Y0 - pad <= y <= Y1 + pad

print('--- pads ---')
for fp in board.GetFootprints():
    for pad in fp.Pads():
        pv = pad.GetPosition()
        p = (mm(pv.x), mm(pv.y))
        if not inbox(*p):
            continue
        sx, sy = mm(pad.GetSize())
        print(f'  {fp.GetReference()}.{pad.GetNumber()} [{pad.GetNetname()}] '
              f'({p[0]:.3f},{p[1]:.3f}) {sx:.2f}x{sy:.2f} '
              f'rot{pad.GetOrientationDegrees():.0f}')
print('--- tracks/vias ---')
LAYN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
        pcbnew.B_Cu: 'B'}
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        pv = t.GetPosition()
        p = (mm(pv.x), mm(pv.y))
        if not inbox(*p):
            continue
        print(f'  VIA [{t.GetNetname()}] ({p[0]:.3f},{p[1]:.3f}) '
              f'd{mm(t.GetWidth()):.2f}/drill{mm(t.GetDrillValue()):.2f}')
    else:
        a = (mm(t.GetStart().x), mm(t.GetStart().y))
        b = (mm(t.GetEnd().x), mm(t.GetEnd().y))
        if not (inbox(*a, 0.5) or inbox(*b, 0.5)):
            continue
        ln = LAYN.get(t.GetLayer(), str(t.GetLayer()))
        print(f'  SEG {ln} [{t.GetNetname()}] ({a[0]:.3f},{a[1]:.3f})->'
              f'({b[0]:.3f},{b[1]:.3f}) w{mm(t.GetWidth()):.2f}')
