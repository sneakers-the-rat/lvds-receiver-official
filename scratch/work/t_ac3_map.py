"""t_ac3: ASCII reach map under t_ab2's DRC-rule model.

Usage: xvfb-run -a python3 scratch/work/t_ac3_map.py BOARD NET SPAD GPAD \
       BX0 BX1 BY0 BY1 MX0 MX1 MY0 MY1
Grids/floods computed over box B*; map printed over sub-box M*.
Chars: S start flood only, G goal flood only, * both, # blocked
(track cell not passable), . free but unreached.
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

CELL = 0.125
TRK_HW = 0.1
VIA_R = 0.25
EPS_GRID = 0.004

src, net, sp, gp = sys.argv[1:5]
X0, X1, Y0, Y1 = map(float, sys.argv[5:9])
MX0, MX1, MY0, MY1 = map(float, sys.argv[9:13])
board = pcbnew.LoadBoard(src)
items, _pc = repair.build_items(board)

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

def cxy(i, j):
    return (X0 + i * CELL, Y0 + j * CELL)

def pair_clr(n, other):
    return max(netclass(n)[1], netclass(other)[1] if other else 0.2)

def pt_clear(li, x, y, rad, eps):
    seen = set()
    for it in items[li].near(li, x, y):
        if it[1] == net or id(it) in seen:
            continue
        seen.add(id(it))
        if dist_to_item(it, x, y) < rad + pair_clr(net, it[1]) + eps:
            return False
    return True

trk_ok = [[[False] * NY for _ in range(NX)] for _ in range(3)]
via_ok = [[False] * NY for _ in range(NX)]
for i in range(NX):
    for j in range(NY):
        x, y = cxy(i, j)
        for li in range(3):
            trk_ok[li][i][j] = pt_clear(li, x, y, TRK_HW, EPS_GRID)
        via_ok[i][j] = all(pt_clear(li, x, y, VIA_R, EPS_GRID)
                           for li in range(3))

def pad_cells(desc):
    return {(i, j) for i in range(NX) for j in range(NY)
            if dist_to_item(pad_item[desc], *cxy(i, j)) <= 0.03}

def flood(seeds):
    from collections import deque
    seen = [set() for _ in range(3)]
    dq = deque()
    for (i, j) in seeds:
        for li in range(3):
            if (i, j) not in seen[li]:
                seen[li].add((i, j)); dq.append((i, j, li))
    while dq:
        i, j, li = dq.popleft()
        if via_ok[i][j]:
            for nl in range(3):
                if nl != li and (i, j) not in seen[nl]:
                    seen[nl].add((i, j)); dq.append((i, j, nl))
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if not (0 <= ni < NX and 0 <= nj < NY):
                    continue
                if not trk_ok[li][ni][nj]:
                    continue
                if di and dj and not (trk_ok[li][i][nj] and
                                      trk_ok[li][ni][j]):
                    continue
                if (ni, nj) not in seen[li]:
                    seen[li].add((ni, nj)); dq.append((ni, nj, li))
    return seen

S = flood(pad_cells(sp))
G = flood(pad_cells(gp))

def cell_of(x, y):
    return (int(round((x - X0) / CELL)), int(round((y - Y0) / CELL)))

ia, ib = cell_of(MX0, MY0)[0], cell_of(MX1, MY0)[0]
ja, jb = cell_of(MX0, MY0)[1], cell_of(MX0, MY1)[1]
for li, ln in enumerate(('F', 'In2', 'B')):
    print(f'--- layer {ln} (x {MX0}..{MX1} left-to-right, '
          f'y {MY0}..{MY1} top-to-bottom) ---')
    print('     ' + ''.join(str(int(cxy(i, ja)[0]) % 10)
                            for i in range(ia, ib + 1)))
    for j in range(ja, jb + 1):
        row = ''
        for i in range(ia, ib + 1):
            s = (i, j) in S[li]; g = (i, j) in G[li]
            if s and g:
                row += '*'
            elif s:
                row += 'S'
            elif g:
                row += 'G'
            elif trk_ok[li][i][j]:
                row += '.'
            else:
                row += '#'
        print(f'{cxy(ia, j)[1]:6.2f} {row}')
