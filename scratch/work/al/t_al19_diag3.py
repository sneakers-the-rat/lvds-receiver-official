import sys, math, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.ToMM
for fp in b.GetFootprints():
    if fp.GetReference() == 'X1':
        for pad in fp.Pads():
            x, y = MM(pad.GetPosition()); sx, sy = MM(pad.GetSize())
            print(f'X1.{pad.GetPadName()} ({x:.2f},{y:.2f}) size {sx:.2f}x{sy:.2f} rot {pad.GetOrientationDegrees()} layers F={pad.IsOnLayer(pcbnew.F_Cu)} net {pad.GetNetname()}')
    if fp.GetReference() == 'C16':
        bb = fp.Reference().GetBoundingBox()
        print(f'C16 ref anchor {MM(fp.Reference().GetPosition().x):.2f},{MM(fp.Reference().GetPosition().y):.2f} bbox x[{MM(bb.GetLeft()):.3f},{MM(bb.GetRight()):.3f}] y[{MM(bb.GetTop()):.3f},{MM(bb.GetBottom()):.3f}] rot {fp.Reference().GetTextAngleDegrees()}')
