#!/usr/bin/env python3
"""Boxed-pad classifier — ONE definition of "boxed", run on both the
before (pass-10 placement) and after (placement-relief) boards.

WHAT IT COMPUTES
  For every pad of every non-GND multi-pad net: the pad's first-move
  fanout (legal fanout target cells, router6 exact shape-distance
  clearance model — the identical fanout_targets() construction used
  by hw/diagnose_groups.py, imported verbatim) and whether the pad
  has ANY legal first move under that model on the layers it occupies
  (fanout cells > 0, or a one-step grid move with non-negative
  margin, or a legal via at the pad).

    BOXED  := fanout == 0 AND reach_from_pad_cells <= n_pad_cells + 4
              (the NO_EXIT test of hw/diagnose_groups.py, verbatim)
    OPEN   := at least one legal first move exists

  On an UNROUTED board every pad is its own connectivity group and a
  pad-to-pad BFS is meaningless (the pass-8 diagnosis relied on the
  routed main group), so unlike diagnose_groups.py this script runs
  NO flood BFS: the placement question is purely "can this pad make
  a legal first move at all", which is decided by the fanout census
  plus the bounded reach test above (that reach only ever explores
  the pad's own sealed neighbourhood: with fanout == 0 it cannot
  escape, so the test is cheap and exact). When fanout > 0 the pad
  is OPEN by definition and no reach is needed.

  Cross-reference (validation): run on an unrouted board, every pad
  the routed-board diagnosis (hw/diagnose_groups.py on the pass-10
  checkpoint board) classified NO_EXIT must also classify BOXED
  here when the routed copper of the same net is absent — pads that
  were POCKET on the routed board may legitimately differ here:
  routed foreign copper only ever ADDS obstacles, so a pad boxed on
  the bare placement is boxed under routing too (monotonicity), and
  a pad open on the bare placement may still have been pocketed by
  routed copper (an ordering problem, not a placement one).

Run: xvfb-run -a python3 results/alt-paths/classify_boxed.py BOARD \
        [OUT.txt]
"""
import sys, time
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair, router6
from router import netclass, cell_of, W, H
from diagnose_groups import fanout_targets

def classify_board(path):
    board = pcbnew.LoadBoard(path)
    items, pad_cells = repair.build_items(board)
    rows = []
    for net in sorted(pad_cells):
        if net == "GND":
            continue
        pins = pad_cells[net]
        if len(pins) < 2:
            continue
        width, clr = netclass(net)
        neck_pts = [p[2] for p in pins]
        anchors = {}
        for _, cs, pos in pins:
            for c in cs:
                anchors[c] = pos
        for desc, cs, pos in pins:
            ftargets = set()
            for s in cs:
                if s in anchors:
                    ftargets |= fanout_targets(items, s, anchors[s],
                                               net, width, clr,
                                               neck_pts)
            fc = len(ftargets)
            if fc > 0:
                rows.append((net, desc, "OPEN", fc, None))
                continue
            # fanout == 0: bounded reach test (diagnose_groups'
            # NO_EXIT condition needs reach; with no fanout targets
            # the flood can only creep to immediately adjacent legal
            # cells, so cap is a safety net, never a factor)
            seen = set(cs)
            frontier = list(seen)
            steps = ((1, 0), (-1, 0), (0, 1), (0, -1),
                     (1, 1), (1, -1), (-1, 1), (-1, -1))
            vr = router6.via_size(width)[0] / 2
            while frontier and len(seen) < 5000:
                nxt = []
                for (li, cx, cy) in frontier:
                    ax, ay = ((cx + 0.5) * router6.CELL,
                              (cy + 0.5) * router6.CELL)
                    for dx, dy in steps:
                        nx, ny = cx + dx, cy + dy
                        if not (0 <= nx < W and 0 <= ny < H):
                            continue
                        nb = (li, nx, ny)
                        if nb in seen:
                            continue
                        bx, by = ((nx + 0.5) * router6.CELL,
                                  (ny + 0.5) * router6.CELL)
                        hw_ = router6._neck_hw(width, ax, ay, bx, by,
                                               neck_pts)
                        if router6.seg_margin(items, li, net, clr,
                                              ax, ay, bx, by,
                                              hw_) < router6.SAFE:
                            continue
                        seen.add(nb); nxt.append(nb)
                    if 2 <= cx <= W - 3 and 2 <= cy <= H - 3:
                        vx, vy = ((cx + 0.5) * router6.CELL,
                                  (cy + 0.5) * router6.CELL)
                        if router6.via_margin(items, net, clr,
                                              vx, vy, vr) >= router6.SAFE:
                            for lj in range(3):
                                nb = (lj, cx, cy)
                                if nb not in seen:
                                    seen.add(nb); nxt.append(nb)
                frontier = nxt
            reach = len(seen)
            cls = "BOXED" if reach <= len(cs) + 4 else "OPEN"
            rows.append((net, desc, cls, fc, reach))
    return rows

def main():
    path = sys.argv[1]
    out = open(sys.argv[2], 'w') if len(sys.argv) > 2 else sys.stdout
    t0 = time.time()
    rows = classify_board(path)
    boxed = [r for r in rows if r[2] == "BOXED"]
    print(f"# board: {path}", file=out)
    print(f"# pads classified: {len(rows)}  BOXED: {len(boxed)}  "
          f"OPEN: {len(rows) - len(boxed)}  ({time.time()-t0:.0f}s)",
          file=out)
    for net, desc, cls, fc, reach in rows:
        r = f" reach={reach}" if reach is not None else ""
        print(f"{cls:6s} {net:12s} {desc:12s} fanout={fc}{r}", file=out)
    if out is not sys.stdout:
        out.close()

if __name__ == "__main__":
    main()
