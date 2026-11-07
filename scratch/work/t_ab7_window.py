"""t_ab7: via-window hunt between the two floods.

For every (x,y) column where one layer's cell is in the START
flood and another layer's cell is in the GOAL flood, report the
column and name the items that make via_ok fail there (or note
via_ok already true — impossible if floods are honest). Closest
columns to the wall (min over layers of flood-boundary distance)
printed first.
Usage: t_ab7_window.py BOARD NET START GOAL X0 X1 Y0 Y1 [EPS]
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

# precompute item distance fields per layer on demand via near()
def blockers(li, x, y, rad):
    out = []
    seen = set()
    for it in items[li].near(li, x, y):
        if it[1] == net or id(it) in seen:
            continue
        seen.add(id(it))
        d = dist_to_item(it, x, y)
        need = rad + pair_clr(it[1]) + EPS
        if d < need + 0.35:
            out.append((d - need, it, d, need))
    return sorted(out)

trk_ok = [[[False] * NY for _ in range(NX)] for _ in range(3)]
via_ok = [[False] * NY for _ in range(NX)]
def pt_clear(li, x, y, rad):
    return all(m >= 0 for (m, _i, _d, _n) in
               [(0, 0, 0, 0)] ) if False else _pt_clear(li, x, y, rad)
def _pt_clear(li, x, y, rad):
    seen = set()
    for it in items[li].near(li, x, y):
        if it[1] == net or id(it) in seen:
            continue
        seen.add(id(it))
        if dist_to_item(it, x, y) < rad + pair_clr(it[1]) + EPS:
            return False
    return True

for i in range(NX):
    for j in range(NY):
        x, y = cxy(i, j)
        for li in range(3):
            trk_ok[li][i][j] = _pt_clear(li, x, y, TRK_HW)
        via_ok[i][j] = all(_pt_clear(li, x, y, VIA_R) for li in range(3))

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
Ss = {(i, j): {l for (a, b, l) in S if (a, b) == (i, j)} for (i, j, l) in S}
Gs = {}
for (i, j, l) in G:
    Gs.setdefault((i, j), set()).add(l)
cands = []
for (i, j), sl in Ss.items():
    gl = Gs.get((i, j), set())
    if gl and not (sl & gl):
        x, y = cxy(i, j)
        worst = 9.9
        for li in range(3):
            bl = blockers(li, x, y, VIA_R)
            if bl:
                worst = min(worst, bl[0][0])
        cands.append((worst, i, j, sl, gl))
cands.sort(reverse=True)
print(f'{len(cands)} mixed columns; cluster map (2mm bins, best margin):')
bins = {}
for (worst, i, j, sl, gl) in cands:
    x, y = cxy(i, j)
    k = (int(x // 2) * 2, int(y // 2) * 2)
    if k not in bins or worst > bins[k][0]:
        bins[k] = (worst, x, y, sl, gl)
for k in sorted(bins, key=lambda k: -bins[k][0]):
    w, x, y, sl, gl = bins[k]
    print(f'  bin {k}: best {w:+.3f} at ({x:.2f},{y:.2f}) start {sorted(sl)} '
          f'goal {sorted(gl)}')
print('top by worst via margin:')
for (worst, i, j, sl, gl) in cands[:20]:
    x, y = cxy(i, j)
    print(f'({x:.3f},{y:.3f}) worst margin {worst:+.3f} start {sorted(sl)} '
          f'goal {sorted(gl)} via_ok={via_ok[i][j]}')
    for li in range(3):
        for (m, it, d, need) in blockers(li, x, y, VIA_R):
            if m < 0.1:
                print(f'   L{li} margin {m:+.3f} {it[0]} {it[1]} '
                      f'd={d:.3f} need={need:.3f} '
                      f'{tuple(round(v, 2) for v in it[2])}')
