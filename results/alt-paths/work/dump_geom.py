import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
print("== board outline ==")
bb = b.GetBoardEdgesBoundingBox()
print(f"edges bbox mm: x {pcbnew.ToMM(bb.GetLeft()):.2f}..{pcbnew.ToMM(bb.GetRight()):.2f}  y {pcbnew.ToMM(bb.GetTop()):.2f}..{pcbnew.ToMM(bb.GetBottom()):.2f}")
targets = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
print("== footprints (ref, x, y, rot, n_pads) sorted by x ==")
rows = []
for fp in b.GetFootprints():
    p = fp.GetPosition()
    rows.append((pcbnew.ToMM(p.x), pcbnew.ToMM(p.y), fp.GetReference(), fp.GetOrientationDegrees(), len(fp.Pads())))
for x, y, ref, rot, np_ in sorted(rows):
    mark = " <== TARGET" if targets and ref in targets else ""
    print(f"{ref:6s} ({x:6.2f},{y:6.2f}) rot={rot:6.1f} pads={np_}{mark}")
