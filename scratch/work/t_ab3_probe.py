"""t_ab3: reachability probe for t_ab2's DRC-rule grid model.

Floods from the start pad (with via transitions) and reports
reachable cell counts per layer, whether any goal cell is
reached, and ASCII maps of trk_ok around key slices.
Usage: t_ab3_probe.py BOARD NET START GOAL X0 X1 Y0 Y1 [EPS]
"""
import math, os, sys
sys.path.insert(0, 'hw')
import pcbnew
import repair, router
from router import netclass, dist_to_item

MM = pcbnew.FromMM
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

starts = [(i, j, 0) for i in range(NX) for j in range(NY)
          if dist_to_item(pad_item[start_desc], *cxy(i, j)) <= 0.03]
goals = {(i, j, 0) for i in range(NX) for j in range(NY)
         if dist_to_item(pad_item[goal_desc], *cxy(i, j)) <= 0.03}
print(f'starts={len(starts)} goals={len(goals)} EPS={EPS}')
seen = set(starts)
stack = list(starts)
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
for li in range(3):
    print(f'layer {li}: reachable {sum(1 for s in seen if s[2] == li)}')
print('goal reached:', bool(seen & goals))
gi, gj, _ = next(iter(goals)) if goals else (0, 0, 0)
print(f'goal cell example {cxy(gi, gj)} trk_ok F={trk_ok[0][gi][gj]} '
      f'via_ok={via_ok[gi][gj]}')
si, sj, _ = starts[0]
print(f'start cell example {cxy(si, sj)}')

def show(li, xa, xb, ya, yb, tag):
    print(f'--- {tag} layer {li} (x {xa}..{xb}, y {ya}..{yb}) '
          f'(.=ok #=wall S=start G=goal-cell)')
    ia = int(round((xa - X0) / CELL)); ib = int(round((xb - X0) / CELL))
    ja = int(round((ya - Y0) / CELL)); jb = int(round((yb - Y0) / CELL))
    sset = {(a, b) for a, b, _ in starts}; gset = {(a, b) for a, b, _ in goals}
    for j in range(ja, jb + 1):
        row = ''
        for i in range(ia, ib + 1):
            if (i, j) in sset: row += 'S'
            elif (i, j) in gset: row += 'G'
            elif not trk_ok[li][i][j]: row += '#'
            elif (i, j, li) in seen: row += '.'
            else: row += ' '
        print(f'y={Y0 + j * CELL:7.3f} {row}')

# full-box maps to file
with open('scratch/work/t_ab3_maps.txt', 'w') as fh:
    for li in range(3):
        fh.write(f'===== layer {li} full box (S=start G=goal .=reached)\n')
        sset = {(a, b) for a, b, _ in starts}
        gset = {(a, b) for a, b, _ in goals}
        for j in range(NY):
            row = ''
            for i in range(NX):
                if (i, j) in sset: row += 'S'
                elif (i, j) in gset: row += 'G'
                elif not trk_ok[li][i][j]: row += '#'
                elif (i, j, li) in seen: row += '.'
                else: row += ' '
            fh.write(f'y={Y0 + j * CELL:7.3f} {row}\n')
print('maps -> scratch/work/t_ab3_maps.txt')
