"""t_ac14: F-only flood from a pad; list via_ok cells inside it.

Control question for the groute NO PATH: can the pad's F region
reach ANY cell where a via is legal? (groute starts on F and can
only change layer at via_ok cells.)

Usage: xvfb-run -a python3 scratch/work/t_ac14_fexit.py BOARD NET PAD X0 X1 Y0 Y1
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

CELL = 0.125
src, net, desc = sys.argv[1], sys.argv[2], sys.argv[3]
X0, X1, Y0, Y1 = map(float, sys.argv[4:8])
board = pcbnew.LoadBoard(src)
items, _pc = repair.build_items(board)

pad_item = None
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        if f'{ref}.{pad.GetNumber()}' == desc:
            pos = pcbnew.ToMM(pad.GetPosition())
            size = pcbnew.ToMM(pad.GetSize())
            pad_item = ('pad', pad.GetNetname(),
                        (pos[0], pos[1], size[0] / 2, size[1] / 2,
                         math.radians(pad.GetOrientationDegrees())), 0.2)
assert pad_item

def pair_clr(other):
    return max(netclass(net)[1], netclass(other)[1] if other else 0.2)

def pt_clear(li, x, y, rad, eps=0.004):
    seen = set()
    for it in items[li].near(li, x, y):
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

from collections import deque
seen = set()
dq = deque()
for i in range(NX):
    for j in range(NY):
        x, y = cxy(i, j)
        if dist_to_item(pad_item, x, y) <= 0.03:
            seen.add((i, j)); dq.append((i, j))
print(f'pad seed cells: {len(seen)}')
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
            if not pt_clear(0, x, y, 0.1):
                continue
            if di and dj:
                xa, ya = cxy(i, nj); xb, yb = cxy(ni, j)
                if not (pt_clear(0, xa, ya, 0.1) and
                        pt_clear(0, xb, yb, 0.1)):
                    continue
            seen.add((ni, nj)); dq.append((ni, nj))
print(f'F flood cells: {len(seen)}')
vias = []
for (i, j) in seen:
    x, y = cxy(i, j)
    if all(pt_clear(li, x, y, 0.25) for li in range(3)):
        vias.append((x, y))
print(f'via_ok cells inside F flood: {len(vias)}')
for v in vias[:40]:
    print(f'  via_ok at ({v[0]:.3f},{v[1]:.3f})')
