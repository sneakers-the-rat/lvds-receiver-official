"""t_ac2: flood-reach probe under t_ab2_groute's DRC-rule model.

Usage: xvfb-run -a python3 scratch/work/t_ac2_flood.py BOARD NET STARTPAD GOALPAD X0 X1 Y0 Y1
Builds the same passability grids as t_ab2 (trk w0.2, via d0.5,
pair clearances from check_pcb classes), BFS-floods from the start
pad and from the goal pad (through vias), and reports per-layer
reach counts, whether the window point cells are reached, and the
southernmost reached row per layer inside a district x-strip.
Extra env: PROBE=x,y;x,y points to test for reach from each side.
"""
import math, os, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair, router
from router import netclass, dist_to_item

MM = pcbnew.FromMM
CELL = 0.125
TRK_HW = 0.1
VIA_R = 0.25
EPS_GRID = 0.004

src, net, sp, gp = sys.argv[1:5]
X0, X1, Y0, Y1 = map(float, sys.argv[5:9])
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
    cells = set()
    for i in range(NX):
        for j in range(NY):
            x, y = cxy(i, j)
            if dist_to_item(pad_item[desc], x, y) <= 0.03:
                cells.add((i, j))
    return cells

def flood(seed_cells):
    from collections import deque
    seen = [set() for _ in range(3)]
    dq = deque()
    for (i, j) in seed_cells:
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

def cell_of(x, y):
    return (int(round((x - X0) / CELL)), int(round((y - Y0) / CELL)))

S = flood(pad_cells(sp))
G = flood(pad_cells(gp))
for name, F in (('START', S), ('GOAL', G)):
    print(name, 'reach per layer F/In2/B:',
          [len(F[li]) for li in range(3)])
probes = [(66.5, 30.375), (67.25, 29.625), (69.3, -0.65),
          (74.95, 17.50), (75.875, 17.375), (62.625, 12.75),
          (60.25, 8.5), (71.375, 19.125), (69.25, 27.625)]
extra = os.environ.get('PROBE', '')
if extra:
    for s in extra.split(';'):
        if s.strip():
            probes.append(tuple(map(float, s.split(','))))
for (x, y) in probes:
    i, j = cell_of(x, y)
    print(f'probe ({x},{y}): cell ({i},{j}) start_reach='
          f'{[ (i,j) in S[li] for li in range(3)]} goal_reach='
          f'{[(i,j) in G[li] for li in range(3)]} via_ok={via_ok[i][j]} '
          f'trk_ok={[trk_ok[li][i][j] for li in range(3)]}')
# southernmost reach per layer within x strips, from START
for (xa, xb) in ((70, 78), (64, 70), (58, 64)):
    ia, ib = cell_of(xa, 0)[0], cell_of(xb, 0)[0]
    for li, ln in enumerate(('F', 'In2', 'B')):
        ys = [cxy(i, j)[1] for i in range(ia, ib + 1)
              for j in range(NY) if (i, j) in S[li]]
        if ys:
            print(f'START strip x{xa}-{xb} layer {ln}: '
                  f'ymin {min(ys):.2f} ymax {max(ys):.2f}')
# overlap?
both = sum(1 for li in range(3) for c in S[li] if c in G[li])
print('overlap cells:', both)
