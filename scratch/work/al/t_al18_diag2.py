import sys, math, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.ToMM
def items_in(x0, y0, x1, y1, label):
    print(f'--- {label} ---')
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            x, y = MM(t.GetPosition())
            if x0 - 1 < x < x1 + 1 and y0 - 1 < y < y1 + 1:
                print(f'  VIA {t.GetNetname()} ({x:.2f},{y:.2f}) d{MM(t.GetWidth()):.2f}')
        else:
            a = MM(t.GetStart()); c = MM(t.GetEnd())
            if (x0 - 1 < a[0] < x1 + 1 and y0 - 1 < a[1] < y1 + 1) or (x0 - 1 < c[0] < x1 + 1 and y0 - 1 < c[1] < y1 + 1):
                print(f'  SEG {t.GetNetname()} L{t.GetLayer()} ({a[0]:.2f},{a[1]:.2f})->({c[0]:.2f},{c[1]:.2f}) w{MM(t.GetWidth()):.2f}')
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            x, y = MM(pad.GetPosition())
            if x0 - 1 < x < x1 + 1 and y0 - 1 < y < y1 + 1:
                print(f'  PAD {fp.GetReference()}.{pad.GetPadName()} {pad.GetNetname()} ({x:.2f},{y:.2f})')
    for z in b.Zones():
        if z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.F_Cu):
            polys = z.GetFilledPolysList(pcbnew.F_Cu)
            v = pcbnew.VECTOR2I(pcbnew.FromMM((x0 + x1) / 2), pcbnew.FromMM((y0 + y1) / 2))
            print(f'  GND fill contains centre: {polys.Contains(v)}')
items_in(83.42, 8.90, 86.58, 10.60, 'C16 ref bbox')
items_in(83.54, 16.16, 86.70, 17.85, 'C20 ref bbox')
print('--- silk shape owners near (6.5,38.5) and (7.2,38.9) ---')
for fp in b.GetFootprints():
    for gi in fp.GraphicalItems():
        if gi.GetLayer() == pcbnew.F_SilkS:
            bb = gi.GetBoundingBox()
            cx, cy = MM(bb.GetCenter().x), MM(bb.GetCenter().y)
            if 4 < cx < 10 and 36 < cy < 42:
                print(f'  {fp.GetReference()} shape{gi.GetShape()} bbox x[{MM(bb.GetLeft()):.2f},{MM(bb.GetRight()):.2f}] y[{MM(bb.GetTop()):.2f},{MM(bb.GetBottom()):.2f}]')
print('--- silk shapes crossing SH1 outline edges ---')
for fp in b.GetFootprints():
    if fp.GetReference() == 'SH1':
        continue
    for gi in fp.GraphicalItems():
        if gi.GetLayer() == pcbnew.F_SilkS:
            bb = gi.GetBoundingBox()
            x0, y0, x1, y1 = MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())
            # crosses SH1 east edge x=29.06 (y 30..50) or north edge y=50.06 / south 29.94 / west 2.94
            if (x0 < 29.06 < x1 and 29 < y0 and y1 < 51) or (y0 < 50.06 < y1 and 2 < x0 and x1 < 30) or \
               (y0 < 29.94 < y1 and 2 < x0 and x1 < 30) or (x0 < 2.94 < x1 and 29 < y0 and y1 < 51):
                print(f'  {fp.GetReference()} shape{gi.GetShape()} bbox x[{x0:.2f},{x1:.2f}] y[{y0:.2f},{y1:.2f}]')
