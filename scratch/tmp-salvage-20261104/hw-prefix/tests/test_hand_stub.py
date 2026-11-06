#!/usr/bin/env python3
"""Regression test: hand-placed escape stubs start ON their pads
(regression for the feceb01 floating-stub fix).

Failure history (found at pass 70): hand_stub.find_stub and
hand_via.find computed the stub/neck start distance with the pad
bbox SUPPORT function hx*|ca| + hy*|sa| — the farthest corner's
projection. On diagonal rays that point lies OFF the pad (misses
of 0.1-0.3 mm measured on U6.36/U6.37/U3.3), so the placed stub
floated: the audit saw it as a lone track group, still
unconnected. The fix uses the true ray-exit distance
min(hx/|ca|, hy/|sa|) minus an inset, so the start is always
inside the pad copper.

Fixture: a QFP-style target pad (1.475 x 0.3 mm) boxed on all
four cardinal directions by foreign bars, so the winning escape
is necessarily diagonal — the case the bug lived in. The test
asserts the returned stub/neck start point lies inside the pad
rectangle (zero distance within tolerance), for both
hand_stub.find_stub and hand_via.find.

Run: xvfb-run -a python3 hw/tests/test_hand_stub.py [HW_DIR]
(HW_DIR defaults to the repo's hw/; point it at a tree with the
pre-fix hand_stub.py/hand_via.py to watch it fail.)
Exit 0 iff every check passes.
"""
import os
import sys

HW = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else \
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HW)
import wx
_app = wx.App(False)
import pcbnew
import hand_stub
import hand_via

MM, TM = pcbnew.FromMM, pcbnew.ToMM
failures = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {detail}")
    if not cond:
        failures.append(name)


board = pcbnew.BOARD()


def add_pad(ref, netname, x, y, sx, sy):
    net = pcbnew.NETINFO_ITEM(board, netname)
    board.Add(net)
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetLayer(pcbnew.F_Cu)
    fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    board.Add(fp)
    pad = pcbnew.PAD(fp)
    pad.SetNumber("1")
    pad.SetShape(pcbnew.PAD_SHAPE_RECT)
    pad.SetSize(pcbnew.VECTOR2I(MM(sx), MM(sy)))
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    pad.SetLayerSet(ls)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetNet(net)
    fp.Add(pad)
    pad.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))


PX, PY = 50.0, 50.0
HX, HY = 0.7375, 0.15          # half of the 1.475 x 0.3 target pad
add_pad("T1", "TGT", PX, PY, 1.475, 0.3)
add_pad("BN", "FRN", PX, 51.6, 6.0, 0.6)     # north bar
add_pad("BS", "FRN", PX, 48.4, 6.0, 0.6)     # south bar
add_pad("BE", "FRN", 52.0, PY, 0.6, 6.0)     # east bar
add_pad("BW", "FRN", 48.35, PY, 0.6, 6.0)    # west bar (segment-close)

items = hand_stub.build_items(board)


def inside(sx, sy):
    return abs(sx - PX) <= HX + 0.001 and abs(sy - PY) <= HY + 0.001


r = hand_stub.find_stub(items, "TGT", (PX, PY), (HX, HY), 0.25)
check("find_stub places a stub", r is not None)
if r is not None:
    sx, sy, ex, ey, w = r
    check("stub start is ON the pad",
          inside(sx, sy),
          f"start ({sx:.3f}, {sy:.3f}) vs pad half "
          f"({HX}, {HY}) at ({PX}, {PY})")
    check("winning escape is diagonal (bug's case)",
          abs(ex - sx) > 0.05 and abs(ey - sy) > 0.05,
          f"dir ({ex - sx:.2f}, {ey - sy:.2f})")

r2 = hand_via.find(items, "TGT", (PX, PY), (HX, HY), 0.25)
check("hand_via finds a via escape", r2 is not None)
if r2 is not None:
    sx, sy = r2[0], r2[1]
    check("via neck start is ON the pad",
          inside(sx, sy),
          f"start ({sx:.3f}, {sy:.3f})")

print("RESULT:", "FAIL" if failures else "PASS",
      f"({len(failures)} failed)")
sys.exit(1 if failures else 0)
