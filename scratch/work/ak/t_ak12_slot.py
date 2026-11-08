"""t_ak12: census of ALL copper (tracks/vias/pads, any net/layer)
intersecting the HV slot rectangle x[12,46] y[23.6,25.1], and GND
zone fill overlap. The slot is a full-depth mill: copper over it
is removed at fab."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
X0, X1, Y0, Y1 = 12.0, 46.0, 23.6, 25.1


def mm(p):
    return pcbnew.ToMM(p)


def seg_hits_rect(a, b):
    # sample the segment
    import math
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.05))
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n
        y = a[1] + (b[1] - a[1]) * k / n
        if X0 <= x <= X1 and Y0 <= y <= Y1:
            return True
    return False


LAY = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
       pcbnew.B_Cu: 'B'}
hits = []
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = mm(t.GetPosition())
        r = mm(t.GetWidth()) / 2
        if x + r >= X0 and x - r <= X1 and y + r >= Y0 and y - r <= Y1:
            hits.append(f'VIA {t.GetNetname()} ({x:.2f},{y:.2f}) '
                        f'd{mm(t.GetWidth()):.2f}')
    else:
        a = mm(t.GetStart())
        b = mm(t.GetEnd())
        if seg_hits_rect(a, b):
            hits.append(f'SEG {LAY.get(t.GetLayer(), "?")} '
                        f'{t.GetNetname()} ({a[0]:.2f},{a[1]:.2f})->'
                        f'({b[0]:.2f},{b[1]:.2f}) '
                        f'w{mm(t.GetWidth()):.2f}')
for fp in board.GetFootprints():
    for p in fp.Pads():
        x, y = mm(p.GetPosition())
        sx, sy = mm(p.GetSize())
        if x + sx / 2 >= X0 and x - sx / 2 <= X1 and \
                y + sy / 2 >= Y0 and y - sy / 2 <= Y1:
            hits.append(f'PAD {fp.GetReference()}.{p.GetPadName()} '
                        f'{p.GetNetname()} ({x:.2f},{y:.2f})')
print(f'{len(hits)} copper items intersect the slot rect:')
for h in sorted(hits):
    print('  ', h)
for z in board.Zones():
    print('zone', z.GetNetname(), 'layers', z.GetLayerSet().FmtHex())
