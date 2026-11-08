import sys, math, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.ToMM
print('--- D1 pads vs silk shapes ---')
for fp in b.GetFootprints():
    if fp.GetReference() == 'D1':
        print(f'  D1 at {MM(fp.GetPosition().x):.2f},{MM(fp.GetPosition().y):.2f} rot {fp.GetOrientationDegrees()}')
        for pad in fp.Pads():
            x, y = MM(pad.GetPosition()); sx, sy = MM(pad.GetSize())
            print(f'  pad {pad.GetPadName()} {pad.GetNetname()} ({x:.2f},{y:.2f}) {sx:.2f}x{sy:.2f}')
        for gi in fp.GraphicalItems():
            if gi.GetLayer() == pcbnew.F_SilkS:
                bb = gi.GetBoundingBox()
                print(f'  silk shape{gi.GetShape()} bbox x[{MM(bb.GetLeft()):.2f},{MM(bb.GetRight()):.2f}] y[{MM(bb.GetTop()):.2f},{MM(bb.GetBottom()):.2f}] w{MM(gi.GetWidth()):.2f}')
print('--- shape owners: polygon near (18.4,50.4), segment near (16,50), rect near (67.2,1.8) ---')
for fp in b.GetFootprints():
    for gi in fp.GraphicalItems():
        if gi.GetLayer() != pcbnew.F_SilkS:
            continue
        bb = gi.GetBoundingBox()
        cx, cy = MM(bb.GetCenter().x), MM(bb.GetCenter().y)
        if (abs(cx - 18.4) < 3 and abs(cy - 50.4) < 3) or (abs(cx - 16) < 3 and abs(cy - 50) < 3) or (abs(cx - 67.2) < 3 and abs(cy - 1.8) < 3):
            print(f'  {fp.GetReference()} shape{gi.GetShape()} bbox x[{MM(bb.GetLeft()):.2f},{MM(bb.GetRight()):.2f}] y[{MM(bb.GetTop()):.2f},{MM(bb.GetBottom()):.2f}] centre ({cx:.1f},{cy:.1f})')
print('--- pads crossed by SH1 rect perimeter (x 2.94..29.06, y 29.94..50.06) ---')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if not pad.IsOnLayer(pcbnew.F_Cu):
            continue
        x, y = MM(pad.GetPosition()); sx, sy = MM(pad.GetSize())
        hx, hy = sx / 2, sy / 2
        # pad rect vs the 4 perimeter lines (as thin bands +-0.1)
        for (lx0, ly0, lx1, ly1, nm) in [(2.94, 29.94, 29.06, 29.94, 'S'), (2.94, 50.06, 29.06, 50.06, 'N'),
                                        (2.94, 29.94, 2.94, 50.06, 'W'), (29.06, 29.94, 29.06, 50.06, 'E')]:
            if nm in 'NS':
                if abs(y - ly0) < hy + 0.1 and x + hx > lx0 and x - hx < lx1:
                    print(f'  {fp.GetReference()}.{pad.GetPadName()} {pad.GetNetname()} ({x:.2f},{y:.2f}) {sx:.2f}x{sy:.2f} crosses {nm} edge')
            else:
                if abs(x - lx0) < hx + 0.1 and y + hy > ly0 and y - hy < ly1:
                    print(f'  {fp.GetReference()}.{pad.GetPadName()} {pad.GetNetname()} ({x:.2f},{y:.2f}) {sx:.2f}x{sy:.2f} crosses {nm} edge')
