"""t_ab13: reconcile t_ab4 flood vs t_ab2 A* reachability on t_ab10.

Builds ONE passability grid, floods from U7.11 (S) and U6.29 (G)
with t_ab4's expansion, then BFS from U7.11 with t_ab2's exact
neighbour rules, and diffs the reached sets.
"""
import math, sys
sys.path.insert(0, 'hw')
import pcbnew
import repair, router
from router import netclass, dist_to_item

CELL = 0.125
TRK_HW, VIA_R = 0.1, 0.25
EPS = 0.004
net = 'ULPI_NXT'
board = pcbnew.LoadBoard('scratch/work/t_ab10.kicad_pcb')
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

X0, X1, Y0, Y1 = 58.0, 82.0, -8.0, 34.0
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
print(f'via_ok={sum(sum(r) for r in via_ok)} '
      f'trk={[sum(sum(r) for r in trk_ok[l]) for l in range(3)]}')

def cells_of(desc):
    return [(i, j, 0) for i in range(NX) for j in range(NY)
            if dist_to_item(pad_item[desc], *cxy(i, j)) <= 0.03]

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
                    if di and dj and not (trk_ok[li][i][nj]
                                          and trk_ok[li][ni][j]):
                        continue
                    cand.append((ni, nj, li))
        for c in cand:
            if c not in seen:
                seen.add(c); stack.append(c)
    return seen

start_cells = cells_of('U7.11')
goal_cells = cells_of('U6.29')
print(f'start cells {len(start_cells)}, goal cells {len(goal_cells)}')
S = flood(start_cells)
G = flood(goal_cells)
print(f'|S|={len(S)} |G|={len(G)} |SxG|={len(S & G)}')
print(f'goal cells in S: {sum(1 for c in goal_cells if c in S)}'
      f'/{len(goal_cells)}')
inter = sorted(S & G)
for c in inter[:10]:
    print('  inter', c, cxy(c[0], c[1]), 'layer', c[2])
# where do S-only and G-only states sit? bounding boxes per layer
for li in range(3):
    so = [(i, j) for (i, j, l) in S - G if l == li]
    go = [(i, j) for (i, j, l) in G - S if l == li]
    if so:
        xs = [cxy(i, j)[0] for i, j in so]; ys = [cxy(i, j)[1] for i, j in so]
        print(f'L{li} S-only {len(so)} x {min(xs):.1f}..{max(xs):.1f} '
              f'y {min(ys):.1f}..{max(ys):.1f}')
    if go:
        xs = [cxy(i, j)[0] for i, j in go]; ys = [cxy(i, j)[1] for i, j in go]
        print(f'L{li} G-only {len(go)} x {min(xs):.1f}..{max(xs):.1f} '
              f'y {min(ys):.1f}..{max(ys):.1f}')
