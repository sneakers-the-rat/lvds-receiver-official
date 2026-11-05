#!/usr/bin/env python3
"""Regression test: the router grid covers the pass-65 expansion
strip (regression for the d4a9e0d grid fix).

Failure history (passes 65-71): hw/router.py's grid stayed sized
for the pre-expansion 100x80 board (W,H = 400,320) and cell_of
clamped y to [0,80]. Every strip item (board y < 0) crushed onto
grid row 0, so strip searches tested phantom geometry along the
old field's north edge: 0-second failures for nets that later
routed in seconds, and vias emitted at y 0.6-2.1. The fix
(d4a9e0d) made the grid 400x440 with OY=-30.

Checks:
  1. grid constants cover the expanded board and OY is -30;
  2. cell_of round-trips a strip point to its true row (with an
     old-field control point that must pass on both versions);
  3. a two-pad strip net on a fixture board routes through the
     production path (repair.build_items/compute_groups +
     router6.astar6/emit6, the heal_nets construction) and the
     emitted copper lies in the strip, not at y ~ 0.

Run: xvfb-run -a python3 hw/tests/test_router_grid.py [HW_DIR]
(HW_DIR defaults to the repo's hw/; point it at a tree with the
pre-fix router.py/router6.py to watch it fail.)
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
import router
import router6
import repair

MM, TM = pcbnew.FromMM, pcbnew.ToMM
failures = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {detail}")
    if not cond:
        failures.append(name)


OY = getattr(router, "OY", 0.0)
check("grid width covers 100 mm", router.W * router.CELL >= 100.0,
      f"W={router.W} CELL={router.CELL}")
check("grid height covers 110 mm", router.H * router.CELL >= 110.0,
      f"H={router.H}")
check("grid origin OY is -30 (strip)", OY == -30.0, f"OY={OY}")

for (x, y) in [(50.0, -15.0), (10.0, -29.0), (86.66, 41.25)]:
    gx, gy = router.cell_of(x, y)
    xr = (gx + 0.5) * router.CELL
    yr = (gy + 0.5) * router.CELL + OY
    check(f"cell_of round-trips ({x}, {y})",
          abs(xr - x) <= router.CELL and abs(yr - y) <= router.CELL,
          f"-> cell ({gx}, {gy}) -> ({xr:.2f}, {yr:.2f})")

# ---- fixture: two pads of one net in the strip, empty field ----
board = pcbnew.BOARD()
net = pcbnew.NETINFO_ITEM(board, "STRIPNET")
board.Add(net)


def add_pad(ref, x, y):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetLayer(pcbnew.F_Cu)
    fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    board.Add(fp)
    pad = pcbnew.PAD(fp)
    pad.SetNumber("1")
    pad.SetShape(pcbnew.PAD_SHAPE_RECT)
    pad.SetSize(pcbnew.VECTOR2I(MM(1.0), MM(0.5)))
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    pad.SetLayerSet(ls)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetNet(net)
    fp.Add(pad)
    pad.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))


add_pad("A1", 50.0, -20.0)
add_pad("A2", 60.0, -20.0)

items, pad_cells = repair.build_items(board)
groups = repair.compute_groups(board).get("STRIPNET", [])
check("fixture has two STRIPNET groups", len(groups) == 2,
      f"got {len(groups)}")
if len(groups) == 2:
    gs = sorted(groups, key=len, reverse=True)
    main_cells = set()
    for it in gs[0]:
        main_cells |= it.cells
    starts = []
    for it in gs[1]:
        if it.kind == "pad":
            starts += list(it.cells)
    if not starts:
        for it in gs[1]:
            starts += list(it.cells)[:2]
    width, clr = router.netclass("STRIPNET")
    neck_pts = [p[2] for p in pad_cells.get("STRIPNET", [])]
    anchors = {}
    for _, cs, pos in pad_cells.get("STRIPNET", []):
        for c in cs:
            anchors[c] = pos
    rpath, fb, lb = router6.astar6(
        items, starts, main_cells, "STRIPNET", width, clr,
        cap=1500000, neck_pts=neck_pts, anchors=anchors)
    check("astar6 routes the strip net", rpath is not None)
    if rpath is not None:
        st = {"vias": 0, "neck_pts": neck_pts, "anchors": anchors,
              "first_bend": fb, "last_bend": lb}
        router6.emit6(board, net, rpath, width, items,
                      "STRIPNET", clr, st)
        ys = []
        for t in board.GetTracks():
            ys += [TM(t.GetStart().y), TM(t.GetEnd().y)]
        check("emitted copper lies in the strip (y ~ -20)",
              bool(ys) and all(abs(y + 20.0) < 1.0 for y in ys),
              f"track y range {min(ys):.2f}..{max(ys):.2f}"
              if ys else "no tracks")

print("RESULT:", "FAIL" if failures else "PASS",
      f"({len(failures)} failed)")
sys.exit(1 if failures else 0)
