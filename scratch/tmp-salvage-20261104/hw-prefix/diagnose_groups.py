#!/usr/bin/env python3
"""Batch diagnosis of every still-isolated group on a board.

For each non-main group: does its pad have any legal first move
under the exact model (grid steps, fanout edges, via)? How far
does a BFS under the exact model reach from it, and does the
reached set come within 2 cells of the main group's cells?
Classifies each group:
  NO_EXIT      no legal first move at all (placement-boxed)
  POCKET       first moves exist but reach < POCKET_MAX cells
  WIDE_NO_GOAL reach is wide but never nears the main group
               (enclosed region, or the goal side is the wall)
  REACHES      reach touches the main group's halo — a full A*
               should have connected; investigate search/cap

Run: xvfb-run -a python3 hw/diagnose_groups.py [board]
"""
import sys, time
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair, router6
from router import netclass, cell_of, W, H

POCKET_MAX = 2000
BFS_CAP = 600000

def fanout_targets(items, node, anchor, net, width, clr, neck_pts):
    """Legal fanout target cells from an anchored start node
    (same construction as router6.astar6's fanout)."""
    out = set()
    li = node[0]
    for ux, uy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for d in router6.BEND_DS:
            bend = (anchor[0] + ux * d, anchor[1] + uy * d)
            hw1 = router6._neck_hw(width, anchor[0], anchor[1],
                                   bend[0], bend[1], neck_pts)
            if router6.seg_margin(items, li, net, clr,
                                  anchor[0], anchor[1],
                                  bend[0], bend[1], hw1) < router6.SAFE:
                continue
            ccx, ccy = cell_of(bend[0], bend[1])
            for ddx in range(-3, 4):
                for ddy in range(-3, 4):
                    cell = (li, ccx + ddx, ccy + ddy)
                    if not (0 <= cell[1] < W and 0 <= cell[2] < H):
                        continue
                    cp = ((cell[1] + 0.5) * router6.CELL,
                          (cell[2] + 0.5) * router6.CELL)
                    if (cp[0] - bend[0]) ** 2 + \
                       (cp[1] - bend[1]) ** 2 > router6.BEND_REACH ** 2:
                        continue
                    hw2 = router6._neck_hw(width, bend[0], bend[1],
                                           cp[0], cp[1], neck_pts)
                    if router6.seg_margin(items, li, net, clr,
                                          bend[0], bend[1],
                                          cp[0], cp[1],
                                          hw2) >= router6.SAFE:
                        out.add(cell)
    return out

def main(board_path="hw/pdlvds_rx.repaired6b.kicad_pcb"):
    board = pcbnew.LoadBoard(board_path)
    items, pad_cells = repair.build_items(board)
    groups_by_net = repair.compute_groups(board)
    t0 = time.time()
    rows = []
    for net in sorted(groups_by_net):
        gs = groups_by_net[net]
        if len(gs) <= 1 or net == "GND":
            continue
        gs = sorted(gs, key=len, reverse=True)
        main_cells = set()
        for it in gs[0]:
            main_cells |= it.cells
        halo = set()
        for (li, cx, cy) in main_cells:
            for dx in (-2, -1, 0, 1, 2):
                for dy in (-2, -1, 0, 1, 2):
                    halo.add((li, cx + dx, cy + dy))
        width, clr = netclass(net)
        neck_pts = [p[2] for p in pad_cells[net]]
        anchors = {}
        for _, cs, pos in pad_cells[net]:
            for c in cs:
                anchors[c] = pos
        vr = router6.via_size(width)[0] / 2
        for g in gs[1:]:
            pad = next((it for it in g if it.kind == "pad"), g[0])
            starts = list(pad.cells)
            # first-move census + BFS seeds: the pad's cells plus
            # every legal fanout target from them
            ftargets = set()
            for s in starts:
                if s in anchors:
                    ftargets |= fanout_targets(
                        items, s, anchors[s], net, width, clr,
                        neck_pts)
            fc = len(ftargets)
            seen = set(starts) | ftargets
            frontier = list(seen)
            steps = ((1, 0), (-1, 0), (0, 1), (0, -1),
                     (1, 1), (1, -1), (-1, 1), (-1, -1))
            while frontier and len(seen) < BFS_CAP:
                nxt = []
                for (li, cx, cy) in frontier:
                    ax, ay = anchors.get((li, cx, cy),
                                         ((cx + 0.5) * router6.CELL,
                                          (cy + 0.5) * router6.CELL)) \
                        if (li, cx, cy) in anchors else \
                        ((cx + 0.5) * router6.CELL,
                         (cy + 0.5) * router6.CELL)
                    for dx, dy in steps:
                        nx, ny = cx + dx, cy + dy
                        if not (0 <= nx < W and 0 <= ny < H):
                            continue
                        nb = (li, nx, ny)
                        if nb in seen:
                            continue
                        bx, by = (nx + 0.5) * router6.CELL, \
                                 (ny + 0.5) * router6.CELL
                        hw_ = router6._neck_hw(width, ax, ay, bx, by,
                                               neck_pts)
                        if router6.seg_margin(items, li, net, clr,
                                              ax, ay, bx, by,
                                              hw_) < router6.SAFE:
                            continue
                        seen.add(nb); nxt.append(nb)
                    if 2 <= cx <= W - 3 and 2 <= cy <= H - 3:
                        vx, vy = (cx + 0.5) * router6.CELL, \
                                 (cy + 0.5) * router6.CELL
                        if router6.via_margin(items, net, clr,
                                              vx, vy, vr) >= router6.SAFE:
                            for lj in range(3):
                                nb = (lj, cx, cy)
                                if nb not in seen:
                                    seen.add(nb); nxt.append(nb)
                frontier = nxt
            reach = len(seen)
            near = bool(seen & halo)
            if fc == 0 and reach <= len(starts) + 4:
                cls = "NO_EXIT"
            elif reach < POCKET_MAX:
                cls = "POCKET"
            elif near:
                cls = "REACHES"
            else:
                cls = "WIDE_NO_GOAL"
            rows.append((cls, net, pad.desc, reach, fc))
            print(f"{cls:13s} {net:12s} {pad.desc:12s} reach="
                  f"{reach:7d} fanout={fc} ({time.time()-t0:.0f}s)",
                  flush=True)
    from collections import Counter
    print(Counter(r[0] for r in rows))

if __name__ == "__main__":
    main(*sys.argv[1:])
