"""Silk shape surgery v2 (identity coords -- KiCad 8 footprint shape
getters/setters use board coordinates). exp229 -> exp230b.
- SH1: rect -> true outline as segments with pad gaps.
- R7: shorten 2 east segments to end x=28.95.
- D1: rect verticals out by 0.13; delete aperture circle.
- U9: rect verticals out to x 66.93 / 69.57 (clear its pads)."""
import sys, wx
_app = wx.App(False)
import pcbnew
SRC, OUT = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(SRC)
MM, FM = pcbnew.ToMM, pcbnew.FromMM
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}

sh1 = fps['SH1']
rect = None
for gi in list(sh1.GraphicalItems()):
    if gi.GetLayer() == pcbnew.F_SilkS:
        bb = gi.GetBoundingBox()
        if abs(MM(bb.GetLeft()) - 2.94) < 0.1:
            rect = gi
assert rect is not None
W = MM(rect.GetWidth())
sh1.Remove(rect)
SEGS = [
    ((5.30, 29.94), (26.70, 29.94)),
    ((5.30, 50.06), (14.93, 50.06)), ((15.93, 50.06), (16.57, 50.06)),
    ((17.57, 50.06), (17.99, 50.06)), ((21.30, 50.06), (24.68, 50.06)),
    ((25.68, 50.06), (26.32, 50.06)),
    ((2.94, 32.30), (2.94, 47.70)),
    ((29.06, 32.30), (29.06, 37.17)), ((29.06, 38.33), (29.06, 47.70)),
]
for (p, q) in SEGS:
    s = pcbnew.PCB_SHAPE(sh1, pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(FM(p[0]), FM(p[1])))
    s.SetEnd(pcbnew.VECTOR2I(FM(q[0]), FM(q[1])))
    s.SetWidth(FM(W))
    s.SetLayer(pcbnew.F_SilkS)
    sh1.Add(s)
print(f'SH1: rect -> {len(SEGS)} segments (w {W})')

r7 = fps['R7']
n = 0
for gi in r7.GraphicalItems():
    if gi.GetLayer() != pcbnew.F_SilkS:
        continue
    a = (MM(gi.GetStart().x), MM(gi.GetStart().y))
    c = (MM(gi.GetEnd().x), MM(gi.GetEnd().y))
    if abs(a[1] - c[1]) < 0.05 and max(a[0], c[0]) > 29.0:
        if a[0] > c[0]:
            gi.SetStart(pcbnew.VECTOR2I(FM(28.95), FM(a[1])))
        else:
            gi.SetEnd(pcbnew.VECTOR2I(FM(28.95), FM(c[1])))
        n += 1
print(f'R7: shortened {n}')

d1 = fps['D1']
for gi in list(d1.GraphicalItems()):
    if gi.GetLayer() != pcbnew.F_SilkS:
        continue
    bb = gi.GetBoundingBox()
    w_mm = MM(bb.GetRight()) - MM(bb.GetLeft()); h_mm = MM(bb.GetBottom()) - MM(bb.GetTop())
    if abs(w_mm - 0.7) < 0.05 and abs(h_mm - 0.7) < 0.05:
        d1.Remove(gi)
        print('D1: removed aperture circle')
    elif abs(MM(bb.GetLeft()) - 6.44) < 0.05:
        s = gi.GetStart(); e = gi.GetEnd()
        sx, ex = MM(s.x), MM(e.x)
        nsx = sx - 0.13 if sx < 8 else sx + 0.13
        nex = ex - 0.13 if ex < 8 else ex + 0.13
        gi.SetStart(pcbnew.VECTOR2I(FM(nsx), s.y))
        gi.SetEnd(pcbnew.VECTOR2I(FM(nex), e.y))
        print(f'D1: rect x {sx:.2f}->{nsx:.2f}, {ex:.2f}->{nex:.2f}')

u9 = fps['U9']
for gi in u9.GraphicalItems():
    if gi.GetLayer() != pcbnew.F_SilkS:
        continue
    bb = gi.GetBoundingBox()
    if abs(MM(bb.GetLeft()) - 67.19) < 0.05:
        s = gi.GetStart(); e = gi.GetEnd()
        for (pt, setter) in [(s, gi.SetStart), (e, gi.SetEnd)]:
            x = MM(pt.x)
            nx = 66.93 if x < 68.25 else 69.57
            setter(pcbnew.VECTOR2I(FM(nx), pt.y))
        print('U9: rect verticals -> 66.93/69.57')

b.Save(OUT)
print('saved', OUT)
