#!/usr/bin/env python3
"""Debug copy of router6.astar6: identical tests, but on exhaustion
prints the visited set's shape (count + bbox per layer) so the
sealed pocket can be compared with the board's true geometry.

Run: xvfb-run -a python3 scratch/work/astar6_dbg.py BOARD NET REF.PAD
"""
import heapq, math, sys, time
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair
from router import netclass, cell_of, CELL, W, H, OY
import router6
from router6 import seg_margin, via_margin, via_size, _neck_hw, SAFE


def astar6_dbg(items, starts, goals, netname, width, clr, cap=1500000,
               neck_pts=(), via_cost=6, anchors=None):
    anchors = anchors or {}
    starts_set = set(starts)
    vr = via_size(width)[0] / 2
    goalset = set(goals)
    openh = []
    gscore = {}
    came = {}
    for node in starts:
        gscore[node] = 0
        heapq.heappush(openh, (0, node))
    hgoals = sorted(goalset)[::max(1, len(goalset) // 300)] \
        or list(goalset)

    def h(node):
        li, cx, cy = node
        return min(max(abs(cx - gx), abs(cy - gy)) +
                   0.4142 * min(abs(cx - gx), abs(cy - gy))
                   for (_, gx, gy) in hgoals)

    def centre(node):
        return ((node[1] + 0.5) * CELL, (node[2] + 0.5) * CELL + OY)

    bends = {}

    def fanout(anchor_pt, li):
        out = {}
        for ux, uy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for d in router6.BEND_DS:
                bend = (anchor_pt[0] + ux * d, anchor_pt[1] + uy * d)
                hw1 = _neck_hw(width, anchor_pt[0], anchor_pt[1],
                               bend[0], bend[1], neck_pts)
                if seg_margin(items, li, netname, clr,
                              anchor_pt[0], anchor_pt[1],
                              bend[0], bend[1], hw1) < SAFE:
                    continue
                ccx, ccy = cell_of(bend[0], bend[1])
                for ddx in range(-3, 4):
                    for ddy in range(-3, 4):
                        cell = (li, ccx + ddx, ccy + ddy)
                        if not (0 <= cell[1] < W and
                                0 <= cell[2] < H):
                            continue
                        cp = centre(cell)
                        if (cp[0] - bend[0]) ** 2 + \
                           (cp[1] - bend[1]) ** 2 > \
                           router6.BEND_REACH ** 2:
                            continue
                        hw2 = _neck_hw(width, bend[0], bend[1],
                                       cp[0], cp[1], neck_pts)
                        if seg_margin(items, li, netname, clr,
                                      bend[0], bend[1],
                                      cp[0], cp[1], hw2) < SAFE:
                            continue
                        cost = (d + math.hypot(cp[0] - bend[0],
                                               cp[1] - bend[1])) / CELL
                        if cell not in out or cost < out[cell][1]:
                            out[cell] = (bend, cost)
        return out

    fanout_out = {}
    for s in starts_set:
        if s in anchors:
            fanout_out[s] = fanout(anchors[s], s[0])
    goal_finish = {}
    for gnode in goalset:
        if gnode in anchors:
            for cell, (bend, cost) in fanout(anchors[gnode],
                                             gnode[0]).items():
                if cell not in goal_finish or \
                   cost < goal_finish[cell][2]:
                    goal_finish[cell] = (gnode, bend, cost)
    visited = set()
    npop = 0
    t0 = time.time()
    while openh:
        _, node = heapq.heappop(openh)
        npop += 1
        if node in goalset and gscore[node] > 0 or \
           (node in goalset and any(s != node for s in starts)):
            return ('GOAL', npop, len(visited))
        if node in goal_finish and node not in starts_set:
            return ('GOAL_FINISH', npop, len(visited))
        visited.add(node)
        if npop > cap:
            return ('CAP', npop, len(visited))
        li, cx, cy = node
        ax, ay = anchors.get(node, centre(node)) \
            if node in starts_set else centre(node)
        if node in starts_set and node in anchors:
            for nb, (bend, cost) in fanout_out.get(node, {}).items():
                ng = gscore[node] + cost
                if nb in gscore and gscore[nb] <= ng:
                    continue
                gscore[nb] = ng; came[nb] = node
                bends[(node, nb)] = bend
                heapq.heappush(openh, (ng + h(nb), nb))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                       (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            nb = (li, nx, ny)
            ng = gscore[node] + (1 if dx == 0 or dy == 0
                                 else math.sqrt(2))
            if nb in gscore and gscore[nb] <= ng:
                continue
            bx, by = anchors.get(nb, centre(nb)) \
                if nb in goalset else centre(nb)
            hw_ = _neck_hw(width, ax, ay, bx, by, neck_pts)
            if seg_margin(items, li, netname, clr,
                          ax, ay, bx, by, hw_) < SAFE:
                continue
            gscore[nb] = ng; came[nb] = node
            heapq.heappush(openh, (ng + h(nb), nb))
        if 2 <= cx <= W - 3 and 2 <= cy <= H - 3:
            for lj in range(3):
                if lj == li:
                    continue
                nb = (lj, cx, cy)
                ng = gscore[node] + via_cost
                if nb in gscore and gscore[nb] <= ng:
                    continue
                vx, vy = centre(node)
                if via_margin(items, netname, clr, vx, vy, vr) < SAFE:
                    continue
                gscore[nb] = ng; came[nb] = node
                heapq.heappush(openh, (ng + h(nb), nb))
    # exhausted
    print("goal cells visited:", {g: (g in visited) for g in sorted(goalset)})
    for li in (2, 1, 0):
        print(f"-- visited map L{li} (x 72.12..81.12 cols, y 12.12..23.12 rows):")
        for cy in range(168, 213):
            row = ""
            for cx in range(288, 325):
                if (li, cx, cy) in goalset: row += "G"
                elif (li, cx, cy) in visited: row += "#"
                else: row += "."
            print("   " + row)
    box = [(li, cx, cy) for (li, cx, cy) in visited
           if 288 <= cx <= 324 and 168 <= cy <= 212]
    from collections import Counter
    print("visited in district box per layer:", dict(Counter(li for li, _, _ in box)))
    print("gscore size:", len(gscore))
    per = {}
    for (li, cx, cy) in visited:
        per.setdefault(li, []).append((cx, cy))
    print(f"EXHAUSTED in {time.time() - t0:.2f}s, pops={npop}, "
          f"visited={len(visited)}")
    for li, cells in sorted(per.items()):
        xs = [c[0] for c in cells]; ys = [c[1] for c in cells]
        print(f"  layer {li}: {len(cells)} cells, cx {min(xs)}.."
              f"{max(xs)} (x {(min(xs)+0.5)*CELL:.2f}.."
              f"{(max(xs)+0.5)*CELL:.2f}), cy {min(ys)}..{max(ys)} "
              f"(y {(min(ys)+0.5)*CELL+OY:.2f}.."
              f"{(max(ys)+0.5)*CELL+OY:.2f})")
    return ('NONE', npop, len(visited))


def main():
    board_path, net, padref = sys.argv[1], sys.argv[2], sys.argv[3]
    board = pcbnew.LoadBoard(board_path)
    items, pad_cells = repair.build_items(board)
    groups = repair.compute_groups(board)[net]
    groups = sorted(groups, key=len, reverse=True)
    width, clr = netclass(net)
    neck_pts = [p[2] for p in pad_cells.get(net, [])]
    anchors = {}
    for _, cs, p in pad_cells.get(net, []):
        for c in cs:
            anchors[c] = p
    main_cells = set()
    for it in groups[0]:
        main_cells |= it.cells
    print(f"{net}: groups {[len(g) for g in groups]}; main group "
          f"cells per layer: "
          f"{ {li: sum(1 for c in main_cells if c[0] == li) for li in range(3)} }")
    print(f"main group items: {[it.desc for it in groups[0]][:14]}")
    for g in groups[1:]:
        if not any(it.desc == padref for it in g):
            continue
        starts = []
        for it in g:
            starts += list(it.cells)
        print(f"isolated group {[it.desc for it in g]} starts={starts}")
        print(astar6_dbg(items, starts, main_cells, net, width, clr,
                         neck_pts=neck_pts, anchors=anchors))


if __name__ == "__main__":
    main()
