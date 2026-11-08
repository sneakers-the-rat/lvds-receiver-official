"""t_ah3: flood probe in t_ab2_groute's exact passability model.
For a net + two pads on a board: count start/goal cells, flood
from each end (3-layer, via switches at via_ok cells), report
visited counts and whether the floods meet; also list the items
blocking the start pad's immediate neighbourhood."""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

SRC = sys.argv[1]
NET, SPAD, GPAD = sys.argv[2], sys.argv[3], sys.argv[4]
X0, X1, Y0, Y1 = map(float, sys.argv[5:9])
CELL = 0.125
TRK_HW, VIA_R, EPS = 0.1, 0.25, 0.004
board = pcbnew.LoadBoard(SRC)
items, _ = repair.build_items(board)
pad_item = {}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        pos = pcbnew.ToMM(pad.GetPosition())
        size = pcbnew.ToMM(pad.GetSize())
        pad_item[f'{fp.GetReference()}.{pad.GetNumber()}'] = (
            'pad', pad.GetNetname(),
            (pos[0], pos[1], size[0] / 2, size[1] / 2,
             math.radians(pad.GetOrientationDegrees())), 0.2)

def pair_clr(net, other):
    return max(netclass(net)[1], netclass(other)[1] if other else 0.2)

def pt_clear(li, x, y, net, rad):
    for it in items[li].near(li, x, y):
        if it[1] == net:
            continue
        if dist_to_item(it, x, y) < rad + pair_clr(net, it[1]) + EPS:
            return False
    return True

NX = int(round((X1 - X0) / CELL)) + 1
NY = int(round((Y1 - Y0) / CELL)) + 1
def cxy(i, j): return (X0 + i * CELL, Y0 + j * CELL)
trk = [[[False] * NY for _ in range(NX)] for _ in range(3)]
via = [[False] * NY for _ in range(NX)]
for i in range(NX):
    for j in range(NY):
        x, y = cxy(i, j)
        for li in range(3):
            trk[li][i][j] = pt_clear(li, x, y, NET, TRK_HW)
        via[i][j] = all(pt_clear(li, x, y, NET, VIA_R)
                        for li in range(3))

def cells_of(desc):
    out = []
    for i in range(NX):
        for j in range(NY):
            x, y = cxy(i, j)
            if dist_to_item(pad_item[desc], x, y) <= 0.03:
                out.append((i, j))
    return out

def flood(seeds):
    seen = set()
    stack = [(i, j, 0) for (i, j) in seeds]
    seen.update(stack)
    while stack:
        i, j, li = stack.pop()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1),
                       (1, 1), (1, -1), (-1, 1), (-1, -1)):
            ni, nj = i + di, j + dj
            if not (0 <= ni < NX and 0 <= nj < NY):
                continue
            if (ni, nj, li) in seen or not trk[li][ni][nj]:
                continue
            if di and dj and not (trk[li][i + di][j] and
                                  trk[li][i][j + dj]):
                continue
            seen.add((ni, nj, li))
            stack.append((ni, nj, li))
        if via[i][j]:
            for li2 in range(3):
                if li2 != li and (i, j, li2) not in seen and \
                        trk[li2][i][j]:
                    seen.add((i, j, li2))
                    stack.append((i, j, li2))
    return seen

sc, gc = cells_of(SPAD), cells_of(GPAD)
print(f'{NET}: start cells {len(sc)} at {SPAD}, '
      f'goal cells {len(gc)} at {GPAD}')
fs, fg = flood(sc), flood(gc)
print(f'flood from start: {len(fs)} cells; '
      f'from goal: {len(fg)} cells; '
      f'meet: {bool(fs & fg)}')
for nm, fl in (('start', fs), ('goal', fg)):
    per = [sum(1 for (i, j, l) in fl if l == li) for li in range(3)]
    print(f'  {nm} flood per layer F/In2/B: {per}')
# blockers near the start pad: foreign items within 1.2 of centre
cx, cy = pad_item[SPAD][2][0], pad_item[SPAD][2][1]
print(f'--- foreign items within 1.6 of {SPAD} ({cx},{cy}) ---')
for li in range(3):
    for it in items[li].near(li, cx, cy):
        if it[1] == NET:
            continue
        d = dist_to_item(it, cx, cy)
        if d < 1.6:
            print(f'  layer{li} {it[0]} {it[1]} '
                  f'data={tuple(round(v, 3) for v in it[2])} '
                  f'dist_to_centre={d:.3f}')
