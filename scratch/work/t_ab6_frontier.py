"""t_ab6: pocket frontier analysis for t_ab2's DRC-rule model.

Computes start/goal floods (via transitions included), then per
layer lists the start-flood frontier cells closest to goal-flood
cells, naming the foreign items that block the wall cells just
outside the frontier.
Usage: t_ab6_frontier.py BOARD NET START GOAL X0 X1 Y0 Y1 [EPS]
"""
import math, sys
sys.path.insert(0, 'hw')
import pcbnew
import repair, router
from router import netclass, dist_to_item

CELL = 0.125
TRK_HW, VIA_R = 0.1, 0.25
net, start_desc, goal_desc = sys.argv[2], sys.argv[3], sys.argv[4]
X0, X1, Y0, Y1 = map(float, sys.argv[5:9])
EPS = float(sys.argv[9]) if len(sys.argv) > 9 else 0.004

board = pcbnew.LoadBoard(sys.argv[1])
items, _ = repair.build_items(board)
pad_item = {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        pos = pcbnew.ToMM(pad.GetPosition())
        size = pcbnew.ToMM(pad.GetSize())
        pad_item[f'{ref}.{pad.GetNumber()}'] = (
            'pad', pad.GetNetname(),
            (pos[0], pos[1], size[0] / 2, size[1] / 2,
             math.radians(pad.GetOrientationDegrees())), 0.2)

NX = int(round((X1 - X0) / CELL)) + 1
NY = int(round((Y1 - Y0) / CELL)) + 1
def cxy(i, j): return (X0 + i * CELL, Y0 + j * CELL)
def pair_clr(other):
    return max(netclass(net)[1], netclass(other)[1] if other else 0.2)
def pt_clear(li, x, y, rad):
    seen = set()
    for it in items[li].near(li, x, y):
        if it[1] == net or id(it) in seen:
            continue
        seen.add(id(it))
        if dist_to_item(it, x, y) < rad + pair_clr(it[1]) + EPS:
            return False
    return True

trk_ok = [[[False] * NY for _ in range(NX)] for _ in range(3)]
via_ok = [[False] * NY for _ in range(NX)]
for i in range(NX):
    for j in range(NY):
        x, y = cxy(i, j)
        for li in range(3):
            trk_ok[li][i][j] = pt_clear(li, x, y, TRK_HW)
        via_ok[i][j] = all(pt_clear(li, x, y, VIA_R) for li in range(3))

def flood(seeds):
    seen = set(seeds); stack = list(seeds)
    while stack:
        i, j, li = stack.pop()
        cand = []
        if via_ok[i][j]:
            cand += [(i, j, (li + 1) % 3), (i, j, (li + 2) % 3)]
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                ni, nj = i + di, j + dj
                if 0 <= ni < NX and 0 <= nj < NY and trk_ok[li][ni][nj]:
                    if di and dj and not (trk_ok[li][i][nj] and trk_ok[li][ni][j]):
                        continue
                    cand.append((ni, nj, li))
        for c in cand:
            if c not in seen:
                seen.add(c); stack.append(c)
    return seen

def cells_of(desc):
    return [(i, j, 0) for i in range(NX) for j in range(NY)
            if dist_to_item(pad_item[desc], *cxy(i, j)) <= 0.03]

S = flood(cells_of(start_desc))
G = flood(cells_of(goal_desc))
print(f'start {len(S)} goal {len(G)} meet {bool(S & G)}')
for li in range(3):
    sc = [(i, j) for (i, j, l) in S if l == li]
    gc = [(i, j) for (i, j, l) in G if l == li]
    if not sc or not gc:
        print(f'layer {li}: start {len(sc)} goal {len(gc)}'); continue
    xs = [cxy(i, j)[0] for i, j in sc]; ys = [cxy(i, j)[1] for i, j in sc]
    print(f'layer {li}: start cells {len(sc)} x {min(xs):.1f}..{max(xs):.1f} '
          f'y {min(ys):.1f}..{max(ys):.1f}')
    gset = set(gc)
    # frontier: start cells with non-start neighbour on this layer
    sset = set(sc)
    frontier = []
    for (i, j) in sc:
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if (i + di, j + dj) not in sset:
                    frontier.append((i, j)); break
            else:
                continue
            break
    # distance from each frontier cell to goal set (grid steps, coarse)
    scored = []
    for (i, j) in frontier:
        best = 1e9
        for di in range(-24, 25, 2):
            for dj in range(-24, 25, 2):
                if (i + di, j + dj) in gset:
                    best = min(best, math.hypot(di, dj))
        if best < 1e8:
            scored.append((best, i, j))
    scored.sort()
    print(f'  frontier {len(frontier)} cells; closest to goal flood:')
    for best, i, j in scored[:10]:
        x, y = cxy(i, j)
        print(f'   ({x:.3f},{y:.3f}) gap {best * CELL:.2f} mm; wall items:')
        named = {}
        for di in (-2, -1, 0, 1, 2):
            for dj in (-2, -1, 0, 1, 2):
                wx, wy = cxy(i + di, j + dj)
                seen = set()
                for it in items[li].near(li, wx, wy):
                    if it[1] == net or id(it) in seen:
                        continue
                    seen.add(id(it))
                    d = dist_to_item(it, wx, wy)
                    if d < 0.35:
                        key = (it[0], it[1], tuple(round(v, 2) for v in it[2]))
                        named[key] = min(named.get(key, 9), d)
        for (kind, n2, data), d in sorted(named.items(), key=lambda kv: kv[1])[:6]:
            print(f'      {kind} {n2} d={d:.3f} {data}')
