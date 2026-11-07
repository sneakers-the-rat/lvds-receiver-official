"""t_ab28: why doesn't NXT's flood reach the channel on t_ab23?
Checks membership of key cells in the start flood and via_ok
at the dive (74.75,18.6) and window (66.5,30.375) points.
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
board = pcbnew.LoadBoard('scratch/work/t_ab23.kicad_pcb')
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

def cell(x, y):
    return (int(round((x - X0) / CELL)), int(round((y - Y0) / CELL)))

for (x, y) in [(74.75, 18.625), (66.5, 30.375), (67.25, 29.625),
               (68.0, 30.5), (69.75, 29.5)]:
    i, j = cell(x, y)
    print(f'({x},{y}) cell {cxy(i, j)}: via_ok={via_ok[i][j]} '
          f'trk={[trk_ok[l][i][j] for l in range(3)]}')

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

seeds = [(i, j, 0) for i in range(NX) for j in range(NY)
         if dist_to_item(pad_item['U7.11'], *cxy(i, j)) <= 0.03]
S = flood(seeds)
print(f'|S|={len(S)}')
for (x, y) in [(74.75, 18.625), (66.5, 30.375), (68.0, 30.5),
               (69.75, 29.5), (71.5, 20.0)]:
    i, j = cell(x, y)
    print(f'({x},{y}): in S layers '
          f'{[l for l in range(3) if (i, j, l) in S]}')
# B-layer extent of S in the south-east lobe
b_cells = [(cxy(i, j)) for (i, j, l) in S if l == 2
           and cxy(i, j)[0] > 66 and cxy(i, j)[1] > 17]
if b_cells:
    xs = [c[0] for c in b_cells]; ys = [c[1] for c in b_cells]
    print(f'S B cells SE of (66,17): {len(b_cells)} '
          f'x {min(xs):.2f}..{max(xs):.2f} y {min(ys):.2f}..{max(ys):.2f}')
