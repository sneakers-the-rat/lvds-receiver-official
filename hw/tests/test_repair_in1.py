#!/usr/bin/env python3
"""Regression test: repair.py survives copper on In1.Cu and counts
its connectivity (regression for the heal crash found at pass 118).

Failure history (found 2026-11-05, after passes 116-117): the
router's grid model is 3-layer (router.LAYERS = [F_Cu, In2_Cu,
B_Cu]) from the era when In1.Cu carried no tracks at all. Passes
116-117 hand-placed two APD_K hauls on In1.Cu (the empty layer --
audit-clean, committed). From then on EVERY heal_nets/repairg run
died in repair.build_items at `LAYERS.index(t.GetLayer())` with
"ValueError: 1 is not in list", and compute_groups had the same
crash in its seg_cells call. The fix: build_items skips
unmodelled-layer tracks (they are not obstacles on any routed
layer) and compute_groups files their cells under a virtual
layer index 3 -- group union there is shape-based, so an In1
segment still merges the groups it touches.

Fixture: one net chained pad -F track- via -In1 track- via -F
track- pad. The chain is one audit group ONLY if the In1 segment
counts. Checks:
  1. repair.build_items completes (pre-fix: ValueError);
  2. repair.compute_groups completes (pre-fix: ValueError);
  3. the chained net has exactly 1 group;
  4. the In1 track is in that group (not dropped).

Run: xvfb-run -a python3 hw/tests/test_repair_in1.py [HW_DIR]
(HW_DIR defaults to the repo's hw/; point it at a tree with the
pre-fix repair.py to watch checks 1-2 fail.)
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
import repair

MM = pcbnew.FromMM
failures = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {detail}")
    if not cond:
        failures.append(name)


board = pcbnew.BOARD()
net = pcbnew.NETINFO_ITEM(board, "CHAIN")
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
    pad.SetSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0)))
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    pad.SetLayerSet(ls)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetNet(net)
    fp.Add(pad)
    pad.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))


def add_track(x1, y1, x2, y2, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
    t.SetWidth(MM(0.4))
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)
    return t


def add_via(x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(0.6))
    v.SetDrill(MM(0.3))
    v.SetNet(net)
    board.Add(v)


add_pad("P1", 40.0, 40.0)
add_track(40.0, 40.0, 45.0, 40.0, pcbnew.F_Cu)
add_via(45.0, 40.0)
in1_track = add_track(45.0, 40.0, 50.0, 40.0, pcbnew.In1_Cu)
add_via(50.0, 40.0)
add_track(50.0, 40.0, 55.0, 40.0, pcbnew.F_Cu)
add_pad("P2", 55.0, 40.0)

try:
    items, pad_cells = repair.build_items(board)
    check("build_items completes with an In1 track on the board",
          True)
except Exception as e:
    check("build_items completes with an In1 track on the board",
          False, f"raised {type(e).__name__}: {e}")

groups = None
try:
    groups = repair.compute_groups(board)
    check("compute_groups completes with an In1 track on the "
          "board", True)
except Exception as e:
    check("compute_groups completes with an In1 track on the "
          "board", False, f"raised {type(e).__name__}: {e}")

if groups is not None:
    gs = groups.get("CHAIN", [])
    check("chained net is exactly 1 group", len(gs) == 1,
          f"got {len(gs)} groups")
    if len(gs) == 1:
        kinds = sorted(it.kind for it in gs[0])
        check("the In1 track is a member of the group",
              any(it.kind == "track" and
                  it.layers == {pcbnew.In1_Cu} for it in gs[0]),
              f"member kinds: {kinds}")

print("RESULT:", "FAIL" if failures else "PASS",
      f"({len(failures)} failed)")
sys.exit(1 if failures else 0)
