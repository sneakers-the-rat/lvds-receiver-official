#!/usr/bin/env python3
"""Regression test: the router/heal obstacle model must register a
pad with its BOARD-ABSOLUTE orientation, not footprint + pad.

Failure history (found 2026-11-06, pass 151 work): X1 (the CDR
crystal) sits rotated 90 degrees; its pads are 4.5 x 2.0 mm, so on
the board pad 2 spans x[84.75,86.75], y[7.5,12.0]. KiCad 8's
pad.GetOrientationDegrees() already returns that board-absolute
90 degrees, but build_items added the footprint rotation on top
(rot + pad orientation = 180), which for a rectangle is the same
shape as 0: the model held the pad's long axis along X, spanning
y[8.75,10.75] instead. The heal therefore routed CDR_SQUELCH
straight through the real pad's corner (the 2.0 mm run at
y=11.125), producing 6 shorting_items + 5 solder_mask_bridge
violations on exp180 that re-healing faithfully reproduced,
because the model could not see the copper it was hitting.

Fixture: the committed exp180 board itself -- the board that
shorted. Checks, against repair.build_items' Items registry and
router.dist_to_item (the A* obstacle distance):
  1. fixture sanity: X1 pad 2's real bounding box is the rotated
     one above;
  2. a point inside the REAL pad but outside the phantom one,
     (86.0, 11.5), is distance 0 from the modelled pad
     (pre-fix: 0.75 -- the model left it open and heal shorted it);
  3. a point inside the PHANTOM pad but outside the real one,
     (84.0, 9.75), is distance 0.75 from the modelled pad
     (pre-fix: 0 -- the model blocked free copper);
  4. the pad centre is distance 0 (sanity);
  5. an unrotated non-square pad elsewhere on the board keeps its
     exact geometry (the fix must not disturb the 0-degree case).

Run: python3 hw/tests/test_pad_orientation.py [REPAIR_DIR]
(REPAIR_DIR defaults to the live heal tree, scratch/heal8; point
it at a tree with the pre-fix repair.py to watch 2-3 fail.)
No wx preamble: KiCad 8 pcbnew needs none. Exit 0 iff all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
MODDIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else \
    os.path.join(REPO, 'scratch', 'heal8')
sys.path.insert(0, os.path.join(REPO, 'hw'))   # router lives here
sys.path.insert(0, MODDIR)                     # the repair under test
import pcbnew
import router
import repair

failures = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {detail}")
    if not cond:
        failures.append(name)


board = pcbnew.LoadBoard(os.path.join(
    REPO, 'hw', 'pdlvds_rx.exp180.kicad_pcb'))
mm = lambda v: v / 1e6

# --- fixture sanity: X1 pad 2's real geometry -------------------
x1 = {fp.GetReference(): fp for fp in board.GetFootprints()}['X1']
pad2 = [p for p in x1.Pads() if p.GetNumber() == '2'][0]
bb = pad2.GetBoundingBox()
check('fixture: X1.2 real bbox is x[84.75,86.75] y[7.5,12.0]',
      abs(mm(bb.GetLeft()) - 84.75) < 0.01
      and abs(mm(bb.GetRight()) - 86.75) < 0.01
      and abs(mm(bb.GetTop()) - 7.5) < 0.01
      and abs(mm(bb.GetBottom()) - 12.0) < 0.01,
      f"got x[{mm(bb.GetLeft()):.2f},{mm(bb.GetRight()):.2f}] "
      f"y[{mm(bb.GetTop()):.2f},{mm(bb.GetBottom()):.2f}]")

# --- the modelled pad item ---------------------------------------
items, _ = repair.build_items(board)
target = None
for bucket in items[0].buckets.values():
    for it in bucket:
        if it[0] == 'pad' and it[1] == 'XO' \
                and abs(it[2][0] - 85.75) < 0.01 \
                and abs(it[2][1] - 9.75) < 0.01:
            target = it
check('model holds an XO pad item at (85.75, 9.75)', target is not None)
if target is not None:
    d = router.dist_to_item
    check('point inside real pad (86.0, 11.5) is blocked (dist 0)',
          d(target, 86.0, 11.5) == 0.0,
          f"got {d(target, 86.0, 11.5):.3f}")
    check('phantom-only point (84.0, 9.75) is 0.75 mm clear',
          abs(d(target, 84.0, 9.75) - 0.75) < 0.01,
          f"got {d(target, 84.0, 9.75):.3f}")
    check('pad centre (85.75, 9.75) is blocked (dist 0)',
          d(target, 85.75, 9.75) == 0.0,
          f"got {d(target, 85.75, 9.75):.3f}")

# --- guard: an unrotated non-square pad is modelled exactly ------
guard = None
for fp in board.GetFootprints():
    if abs(fp.GetOrientationDegrees()) > 0.01:
        continue
    for p in fp.Pads():
        s = p.GetSize()
        if max(s.x, s.y) > 1.5 * max(1, min(s.x, s.y)) and p.GetNetname():
            guard = (fp, p)
            break
    if guard:
        break
if guard is None:
    check('guard fixture: found an unrotated non-square pad', False)
else:
    fp, p = guard
    gb = p.GetBoundingBox()
    cx = mm(p.GetPosition().x)
    probe_x = mm(gb.GetRight()) + 0.3
    item = None
    for bucket in items[0].buckets.values():
        for it in bucket:
            if it[0] == 'pad' and it[1] == p.GetNetname() \
                    and abs(it[2][0] - cx) < 0.01 \
                    and abs(it[2][1] - mm(p.GetPosition().y)) < 0.01:
                item = it
    got = router.dist_to_item(item, probe_x, mm(p.GetPosition().y)) \
        if item else -1
    check(f'guard: unrotated pad {fp.GetReference()}.{p.GetNumber()} '
          f'probe 0.3 mm east of its edge reads 0.3',
          item is not None and abs(got - 0.3) < 0.02, f'got {got:.3f}')

print('FAILURES:', failures if failures else 'none')
sys.exit(1 if failures else 0)
