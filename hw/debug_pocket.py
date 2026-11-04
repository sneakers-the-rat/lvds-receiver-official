#!/usr/bin/env python3
"""Debug: for one net on a ripped board, list its groups; for each
single-pad group, BFS the cells reachable under the v6 model from
the pad (ignoring goals) and report the pocket size, plus the worst
blocking item for each first step out of the pad cell.
Run: xvfb-run -a python3 hw/debug_pocket.py BOARD NET"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
import router6
from router import netclass, cell_of

board = pcbnew.LoadBoard(sys.argv[1])
net = sys.argv[2]
items, pad_cells = repair.build_items(board)
groups = repair.compute_groups(board)[net]
groups.sort(key=len, reverse=True)
width, clr = netclass(net)
neck_pts = [p[2] for p in pad_cells.get(net, [])]
anchors = {}
for _, cs, pos in pad_cells.get(net, []):
    for c in cs:
        anchors[c] = pos
print(f"{net}: {len(groups)} groups, sizes {[len(g) for g in groups]}")
for g in groups[1:]:
    pads = [it for it in g if it.kind == "pad"]
    if not pads:
        print("  non-pad group:", [it.desc for it in g][:4]); continue
    pad = pads[0]
    starts = list(pad.cells)
    # BFS pocket
    seen = set(starts); stack = list(starts)
    def centre(n): return ((n[1] + 0.5) * router6.CELL, (n[2] + 0.5) * router6.CELL)
    while stack:
        node = stack.pop()
        li, cx, cy = node
        a = anchors.get(node, centre(node)) if node in set(starts) else centre(node)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (li, cx + dx, cy + dy)
            if nb in seen: continue
            if not (0 <= nb[1] < router6.W and 0 <= nb[2] < router6.H): continue
            b = centre(nb)
            hw_ = router6._neck_hw(width, a[0], a[1], b[0], b[1], neck_pts)
            if router6.seg_margin(items, li, net, clr, a[0], a[1], b[0], b[1], hw_) >= router6.SAFE:
                seen.add(nb); stack.append(nb)
        vr = router6.via_size(width)[0] / 2
        vx, vy = centre(node)
        if router6.via_margin(items, net, clr, vx, vy, vr) >= router6.SAFE:
            for lj in range(3):
                nb = (lj, cx, cy)
                if nb not in seen:
                    seen.add(nb); stack.append(nb)
    print(f"  {pad.desc}: pocket {len(seen)} cells")
    # first-step detail from each start cell
    for node in starts:
        li, cx, cy = node
        a = anchors.get(node, centre(node))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (li, cx + dx, cy + dy)
            b = centre(nb)
            hw_ = router6._neck_hw(width, a[0], a[1], b[0], b[1], neck_pts)
            m = router6.seg_margin(items, li, net, clr, a[0], a[1], b[0], b[1], hw_)
            print(f"    step {node}->{nb}: margin {m:+.3f} (hw {hw_})")
        vr = router6.via_size(width)[0] / 2
        vx, vy = centre(node)
        print(f"    via at {node}: margin {router6.via_margin(items, net, clr, vx, vy, vr):+.3f}")
