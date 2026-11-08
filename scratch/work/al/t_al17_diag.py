import sys, math, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.ToMM
# 1) what copper is under C16/C20 ref bboxes?
for refname in ['C16', 'C20', 'U7', 'R17']:
    for fp in b.GetFootprints():
        if fp.GetReference() == refname:
            bb = fp.Reference().GetBoundingBox()
            print(f'{refname} ref bbox x[{MM(bb.GetLeft()):.2f},{MM(bb.GetRight()):.2f}] y[{MM(bb.GetTop()):.2f},{MM(bb.GetBottom()):.2f}] fp at {MM(fp.GetPosition().x):.1f},{MM(fp.GetPosition().y):.1f}')
# 2) board-level drawings on F.SilkS
print('--- board drawings F.SilkS ---')
for dr in b.GetDrawings():
    if dr.GetLayer() == pcbnew.F_SilkS:
        bb = dr.GetBoundingBox()
        print(f'  {dr.GetShape()} bbox x[{MM(bb.GetLeft()):.2f},{MM(bb.GetRight()):.2f}] y[{MM(bb.GetTop()):.2f},{MM(bb.GetBottom()):.2f}]')
# 3) footprint silk shapes with big bboxes (the west rectangle)
print('--- footprint silk shapes with bbox > 8mm ---')
for fp in b.GetFootprints():
    for gi in fp.GraphicalItems():
        if gi.GetLayer() == pcbnew.F_SilkS:
            bb = gi.GetBoundingBox()
            if MM(bb.GetWidth()) > 8 or MM(bb.GetHeight()) > 8:
                print(f'  {fp.GetReference()} {gi.GetShape()} bbox x[{MM(bb.GetLeft()):.2f},{MM(bb.GetRight()):.2f}] y[{MM(bb.GetTop()):.2f},{MM(bb.GetBottom()):.2f}]')
