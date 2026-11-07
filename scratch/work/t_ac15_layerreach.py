"""t_ac15: per-layer flood reach from arbitrary seed cells under
the t_ab2 model — used to test whether a via cell's landing layer
is a pocket or the mainland.

Usage: xvfb-run -a python3 scratch/work/t_ac15_layerreach.py BOARD NET LAYER x,y [x,y ...] -- X0 X1 Y0 Y1
Prints reached-cell count on LAYER and the reach bbox.
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

CELL = 0.125
src, net = sys.argv[1], sys.argv[2]
li = int(sys.argv[3])
seeds_xy = []
k = 4
while sys.argv[k] != '--':
    seeds_xy.append(tuple(map(float, sys.argv[k].split(','))))
    k += 1
X0, X1, Y0, Y1 = map(float, sys.argv[k + 1:k + 5])
board = pcbnew.LoadBoard(src)
items, _pc = repair.build_items(board)

def pair_clr(other):
    return max(netclass(net)[1], netclass(other)[1] if other else 0.2)

def pt_clear(l, x, y, rad, eps=0.004):
    seen = set()
    for it in items[l].near(l, x, y):
        if it[1] == net or id(it) in seen:
            continue
        seen.add(id(it))
        if dist_to_item(it, x, y) < rad + pair_clr(it[1]) + eps:
            return False
    return True

NX = int(round((X1 - X0) / CELL)) + 1
NY = int(round((Y1 - Y0) / CELL)) + 1

def cxy(i, j):
    return (X0 + i * CELL, Y0 + j * CELL)

def cell_of(x, y):
    return (int(round((x - X0) / CELL)), int(round((y - Y0) / CELL)))

from collections import deque
seen = set()
dq = deque()
for (x, y) in seeds_xy:
    i, j = cell_of(x, y)
    if (i, j) not in seen:
        seen.add((i, j)); dq.append((i, j))
while dq:
    i, j = dq.popleft()
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ni, nj = i + di, j + dj
            if not (0 <= ni < NX and 0 <= nj < NY) or (ni, nj) in seen:
                continue
            x, y = cxy(ni, nj)
            if not pt_clear(li, x, y, 0.1):
                continue
            if di and dj:
                xa, ya = cxy(i, nj); xb, yb = cxy(ni, j)
                if not (pt_clear(li, xa, ya, 0.1) and
                        pt_clear(li, xb, yb, 0.1)):
                    continue
            seen.add((ni, nj)); dq.append((ni, nj))
xs = [cxy(i, j)[0] for (i, j) in seen]
ys = [cxy(i, j)[1] for (i, j) in seen]
print(f'layer {li}: reached {len(seen)} cells, '
      f'x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}')
