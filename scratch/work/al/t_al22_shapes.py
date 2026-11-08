"""Silk shape surgery on exp229 -> exp230:
- SH1: replace the can rectangle with the true outline drawn as
  segments with gaps at every pad crossing (own corner pads,
  R8.1 east, R5/R6/U12 pads north, U12 marker).
- R7: shorten its two east silk segments to end x<=28.95.
- D1: widen its outline rect verticals off its pads (x 6.44->6.33,
  9.56->9.67); delete the aperture circle (sits entirely on pad 1's
  mask opening -- unprintable).
- U9: diagnostics only (pads vs rect lines)."""
import sys, math, wx
_app = wx.App(False)
import pcbnew
SRC, OUT = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(SRC)
MM, FM = pcbnew.ToMM, pcbnew.FromMM

def l2b(fp, lx, ly):
    """footprint-local -> board coords."""
    a = math.radians(fp.GetOrientationDegrees())
    x, y = MM(fp.GetPosition().x), MM(fp.GetPosition().y)
    return (x + lx * math.cos(a) - ly * math.sin(a), y + lx * math.sin(a) + ly * math.cos(a))

def b2l(fp, bx, by):
    a = math.radians(-fp.GetOrientationDegrees())
    x, y = MM(fp.GetPosition().x), MM(fp.GetPosition().y)
    dx, dy = bx - x, by - y
    return (dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a))

fps = {fp.GetReference(): fp for fp in b.GetFootprints()}

# ---------- SH1 ----------
sh1 = fps['SH1']
print(f'SH1 at {MM(sh1.GetPosition().x):.2f},{MM(sh1.GetPosition().y):.2f} rot {sh1.GetOrientationDegrees()}')
rect = None
for gi in list(sh1.GraphicalItems()):
    if gi.GetLayer() == pcbnew.F_SilkS:
        bb = gi.GetBoundingBox()
        if abs(MM(bb.GetLeft()) - 2.94) < 0.1 and abs(MM(bb.GetBottom()) - 50.06) < 0.1:
            rect = gi
            print(f'  rect shape{gi.GetShape()} width {MM(gi.GetWidth()):.2f} start {MM(gi.GetStart().x):.2f},{MM(gi.GetStart().y):.2f} end {MM(gi.GetEnd().x):.2f},{MM(gi.GetEnd().y):.2f}')
assert rect is not None
W = MM(rect.GetWidth())
sh1.Remove(rect)
SEGS = [  # board coords, true outline with pad gaps
    ((5.30, 29.94), (26.70, 29.94)),                    # south
    ((5.30, 50.06), (14.93, 50.06)), ((15.93, 50.06), (16.57, 50.06)),
    ((17.57, 50.06), (17.99, 50.06)), ((21.30, 50.06), (24.68, 50.06)),
    ((25.68, 50.06), (26.32, 50.06)),                    # north pieces
    ((2.94, 32.30), (2.94, 47.70)),                      # west
    ((29.06, 32.30), (29.06, 37.17)), ((29.06, 38.33), (29.06, 47.70)),  # east
]
for (p, q) in SEGS:
    s = pcbnew.PCB_SHAPE(sh1, pcbnew.SHAPE_T_SEGMENT)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    lp, lq = b2l(sh1, *p), b2l(sh1, *q)
    s.SetStart(pcbnew.VECTOR2I(FM(lp[0]), FM(lp[1])))
    s.SetEnd(pcbnew.VECTOR2I(FM(lq[0]), FM(lq[1])))
    s.SetWidth(FM(W))
    s.SetLayer(pcbnew.F_SilkS)
    sh1.Add(s)
print(f'  SH1: rect replaced with {len(SEGS)} segments')

# ---------- R7 ----------
r7 = fps['R7']
n = 0
for gi in r7.GraphicalItems():
    if gi.GetLayer() != pcbnew.F_SilkS:
        continue
    a = l2b(r7, MM(gi.GetStart().x), MM(gi.GetStart().y))
    c = l2b(r7, MM(gi.GetEnd().x), MM(gi.GetEnd().y))
    if abs(a[1] - c[1]) < 0.05 and max(a[0], c[0]) > 29.0:  # horizontal seg crossing x29.06
        # shorten the east end to 28.95
        if a[0] > c[0]:
            a = (28.95, a[1])
        else:
            c = (28.95, c[1])
        la, lc = b2l(r7, *a), b2l(r7, *c)
        gi.SetStart(pcbnew.VECTOR2I(FM(la[0]), FM(la[1])))
        gi.SetEnd(pcbnew.VECTOR2I(FM(lc[0]), FM(lc[1])))
        n += 1
print(f'  R7: shortened {n} segments')

# ---------- D1 ----------
d1 = fps['D1']
for gi in list(d1.GraphicalItems()):
    if gi.GetLayer() != pcbnew.F_SilkS:
        continue
    bb = gi.GetBoundingBox()
    bx = (MM(bb.GetLeft()), MM(bb.GetRight())); by = (MM(bb.GetTop()), MM(bb.GetBottom()))
    if gi.GetShape() == 3 or (abs(bx[1] - bx[0] - 0.7) < 0.05 and abs(by[1] - by[0] - 0.7) < 0.05):
        d1.Remove(gi)
        print('  D1: removed aperture circle')
    elif abs(bx[0] - 6.44) < 0.05 and abs(bx[1] - 9.56) < 0.05:
        # rectangle: move start/end x outward by 0.13
        s = gi.GetStart(); e = gi.GetEnd()
        bs = l2b(d1, MM(s.x), MM(s.y)); be = l2b(d1, MM(e.x), MM(e.y))
        bs = (bs[0] - 0.13 if bs[0] < 8 else bs[0] + 0.13, bs[1])
        be = (be[0] - 0.13 if be[0] < 8 else be[0] + 0.13, be[1])
        ls, le = b2l(d1, *bs), b2l(d1, *be)
        gi.SetStart(pcbnew.VECTOR2I(FM(ls[0]), FM(ls[1])))
        gi.SetEnd(pcbnew.VECTOR2I(FM(le[0]), FM(le[1])))
        print(f'  D1: rect verticals moved to x {bs[0]:.2f}/{be[0]:.2f}')

# ---------- U9 diagnostics ----------
u9 = fps['U9']
print(f'U9 at {MM(u9.GetPosition().x):.2f},{MM(u9.GetPosition().y):.2f} rot {u9.GetOrientationDegrees()}')
for pad in u9.Pads():
    x, y = MM(pad.GetPosition()); sx, sy = MM(pad.GetSize())
    print(f'  pad {pad.GetPadName()} ({x:.2f},{y:.2f}) {sx:.2f}x{sy:.2f}')
for gi in u9.GraphicalItems():
    if gi.GetLayer() == pcbnew.F_SilkS:
        bb = gi.GetBoundingBox()
        print(f'  silk shape{gi.GetShape()} bbox x[{MM(bb.GetLeft()):.2f},{MM(bb.GetRight()):.2f}] y[{MM(bb.GetTop()):.2f},{MM(bb.GetBottom()):.2f}]')

b.Save(OUT)
print('saved', OUT)
