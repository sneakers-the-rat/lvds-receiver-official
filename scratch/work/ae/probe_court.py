import sys
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
for fp in b.GetFootprints():
    if fp.GetReference() in ('C20','X1','U5','R45'):
        # courtyard: use the F.CrtYd / B.CrtYd drawing items
        bb = None
        for d in fp.GraphicalItems():
            if d.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                x = d.GetBoundingBox()
                bb = x if bb is None else bb.Merge(x)
        print(fp.GetReference(), 'pos', pcbnew.ToMM(fp.GetPosition()),
              'crt bbox', (round(pcbnew.ToMM(bb.GetLeft()),3), round(pcbnew.ToMM(bb.GetTop()),3),
                           round(pcbnew.ToMM(bb.GetRight()),3), round(pcbnew.ToMM(bb.GetBottom()),3)) if bb else None)
