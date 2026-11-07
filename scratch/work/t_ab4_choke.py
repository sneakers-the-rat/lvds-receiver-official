"""t_ab4: bidirectional flood choke finder for t_ab2's model.

Floods from START pad and from GOAL pad (both with via
transitions), then for each layer reports the closest pair of
cells between the two floods and the foreign items blocking the
gap cells between them.
Usage: t_ab4_choke.py BOARD NET START GOAL X0 X1 Y0 Y1 [EPS]
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
EPS = float(sys.argv[9]) if len(sys.argv) > 9 else 0.045

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
    for it in items[li].near(li, x, y):
        if it[1] == net:
            continue
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
print(f'start flood {len(S)}, goal flood {len(G)}, meet: {bool(S & G)}')
for li in range(3):
    sc = [(i, j) for (i, j, l) in S if l == li]
    gc = {(i, j) for (i, j, l) in G if l == li}
    best = None
    for (i, j) in sc:
        for di in range(-14, 15):
            for dj in range(-14, 15):
                if (i + di, j + dj) in gc:
                    d = math.hypot(di, dj)
                    if best is None or d < best[0]:
                        best = (d, (i, j), (i + di, j + dj))
    if best:
        d, a, b = best
        print(f'layer {li}: closest {d * CELL:.3f} mm between '
              f'{cxy(*a)} (start side) and {cxy(*b)} (goal side)')
        # what blocks the cells between?
        mx, my = (a[0] + b[0]) // 2, (a[1] + b[1]) // 2
        x, y = cxy(mx, my)
        print(f'   gap midpoint {x:.3f},{y:.3f}; blockers there:')
        for it in items[li].near(li, x, y):
            if it[1] == net:
                continue
            dd = dist_to_item(it, x, y)
            if dd < 1.2:
                print(f'     {it[0]} net={it[1]} dist={dd:.3f} data={it[2]}')
    else:
        print(f'layer {li}: floods nowhere within 1.75 mm')
# northmost reach of start flood / southmost of goal flood per layer
for li in range(3):
    sy = [j for (i, j, l) in S if l == li]
    gy = [j for (i, j, l) in G if l == li]
    if sy and gy:
        print(f'layer {li}: start flood y range '
              f'{Y0 + min(sy) * CELL:.2f}..{Y0 + max(sy) * CELL:.2f}; '
              f'goal flood y range {Y0 + min(gy) * CELL:.2f}..'
              f'{Y0 + max(gy) * CELL:.2f}')
