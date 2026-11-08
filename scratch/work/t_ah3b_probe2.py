"""t_ah3b: t_ah3 flood probe + fence analysis.
After flooding from both ends, find the closest same-layer cell pair
between the two floods and list the foreign items near the midpoint --
that names the fence keeping the floods apart."""
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
    for li in range(3):
        pts = [cxy(i, j) for (i, j, l) in fl if l == li]
        if pts:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            print(f'    L{li} bbox x[{min(xs):.2f},{max(xs):.2f}] '
                  f'y[{min(ys):.2f},{max(ys):.2f}]')

# closest same-layer pair between the floods, per layer
fs_by = {li: [(i, j) for (i, j, l) in fs if l == li] for li in range(3)}
fg_by = {li: [(i, j) for (i, j, l) in fg if l == li] for li in range(3)}
best = None
for li in range(3):
    lb = None
    for (i, j) in fs_by[li]:
        for (k, m) in fg_by[li]:
            d2 = (i - k) ** 2 + (j - m) ** 2
            if lb is None or d2 < lb[0]:
                lb = (d2, (i, j), (k, m))
    if lb:
        d2, a, b = lb
        ax, ay = cxy(*a); bx, by = cxy(*b)
        print(f'layer {li}: closest ({ax:.3f},{ay:.3f}) -> '
              f'({bx:.3f},{by:.3f}) gap {math.sqrt(d2)*CELL:.3f} mm')
        if best is None or d2 < best[0]:
            best = (d2, li, a, b)
if best:
    d2, li, a, b = best
    ax, ay = cxy(*a); bx, by = cxy(*b)
    mx, my = (ax + bx) / 2, (ay + by) / 2
    print(f'closest pair: layer {li} start-side ({ax:.3f},{ay:.3f}) '
          f'goal-side ({bx:.3f},{by:.3f}) gap {math.sqrt(d2)*CELL:.3f} mm; '
          f'midpoint ({mx:.3f},{my:.3f})')
    print(f'--- foreign items within 1.3 of midpoint, all layers ---')
    for li2 in range(3):
        for it in items[li2].near(li2, mx, my):
            if it[1] == NET:
                continue
            d = dist_to_item(it, mx, my)
            if d < 1.3:
                print(f'  layer{li2} {it[0]} {it[1]} '
                      f'data={tuple(round(v, 3) for v in it[2])} '
                      f'dist={d:.3f}')
    # which cells between the pair are blocked, per layer
    print('--- cell passability along the pair line, per layer ---')
    steps = max(abs(a[0] - b[0]), abs(a[1] - b[1]))
    for li2 in range(3):
        row = []
        for s in range(steps + 1):
            i = round(a[0] + (b[0] - a[0]) * s / max(steps, 1))
            j = round(a[1] + (b[1] - a[1]) * s / max(steps, 1))
            row.append('T' if trk[li2][i][j] else '.')
        print(f'  L{li2}: {"".join(row)}  (via_ok at mid col: '
              f'{via[round((a[0]+b[0])/2)][round((a[1]+b[1])/2)]})')
