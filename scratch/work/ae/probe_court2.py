import sys
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
for fp in b.GetFootprints():
    if fp.GetReference() in ('C20','X1','U5','R45','C48','C19'):
        poly = fp.GetCourtyard(pcbnew.F_CrtYd)
        bb = poly.BBox()
        print(fp.GetReference(), 'pos', [round(v,3) for v in pcbnew.ToMM(fp.GetPosition())],
              'crt x', round(pcbnew.ToMM(bb.GetLeft()),3), round(pcbnew.ToMM(bb.GetRight()),3),
              'y', round(pcbnew.ToMM(bb.GetTop()),3), round(pcbnew.ToMM(bb.GetBottom()),3))
