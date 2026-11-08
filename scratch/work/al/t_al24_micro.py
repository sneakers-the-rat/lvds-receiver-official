import sys, wx
_app = wx.App(False)
import pcbnew
SRC, OUT = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(SRC)
MM, FM = pcbnew.ToMM, pcbnew.FromMM
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
r7 = fps['R7']
for gi in r7.GraphicalItems():
    if gi.GetLayer() != pcbnew.F_SilkS:
        continue
    for (get, setf) in [(gi.GetStart, gi.SetStart), (gi.GetEnd, gi.SetEnd)]:
        p = get()
        if abs(MM(p.x) - 28.95) < 0.02:
            setf(pcbnew.VECTOR2I(FM(28.88), p.y))
            print('R7 end -> 28.88')
sh1 = fps['SH1']
for gi in list(sh1.GraphicalItems()):
    if gi.GetLayer() != pcbnew.F_SilkS:
        continue
    s = (MM(gi.GetStart().x), MM(gi.GetStart().y))
    if abs(s[0] - 15.93) < 0.02 and abs(s[1] - 50.06) < 0.02:
        sh1.Remove(gi)
        print('SH1: dropped north piece #2')
b.Save(OUT)
print('saved', OUT)
