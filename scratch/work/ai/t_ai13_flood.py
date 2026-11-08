"""t_ai13: grid flood over the exact item model for one onward leg.
Usage: t_ai13_flood.py board NET LAYER(F|In2|B) HW SX SY TX TY \
       X0 X1 Y0 Y1 [OX,OY,OR ...]   (extra via obstacles)
Target = point (TX,TY); reached when a flood cell centre is within
HW+0.05 of it. Prints REACHED or the frontier's blocking items."""
import collections, math, sys
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import load_items, pt_margin, in_box_pool, fmt_it

board = pcbnew.LoadBoard(sys.argv[1])
NET = sys.argv[2]
LI = {'F': 0, 'In2': 1, 'B': 2}[sys.argv[3]]
HW = float(sys.argv[4])
S = (float(sys.argv[5]), float(sys.argv[6]))
T = (float(sys.argv[7]), float(sys.argv[8]))
X0, X1, Y0, Y1 = map(float, sys.argv[9:13])
OBS = []
for a in sys.argv[13:]:
    ox, oy, orr = map(float, a.split(','))
    OBS.append((ox, oy, orr))
items = load_items(board)
pool = in_box_pool(items, (X0, X1, Y0, Y1), pad=1.2)[LI]
STEP = 0.0625
NX = int(round((X1 - X0) / STEP)) + 1
NY = int(round((Y1 - Y0) / STEP)) + 1
print(f'grid {NX}x{NY}, pool {len(pool)} items')

passable = {}
for ix in range(NX):
    for iy in range(NY):
        x, y = X0 + ix * STEP, Y0 + iy * STEP
        m, _ = pt_margin(LI, x, y, NET, HW, pool)
        if m < 0:
            continue
        ok = True
        for (ox, oy, orr) in OBS:
            if math.hypot(x - ox, y - oy) - orr - HW - 0.25 < 0:
                ok = False
                break
        if ok:
            passable[(ix, iy)] = m
print(f'passable cells: {len(passable)}')

si = (int(round((S[0] - X0) / STEP)), int(round((S[1] - Y0) / STEP)))
seen = {si}
dq = collections.deque([si])
parent = {si: None}
while dq:
    c = dq.popleft()
    if math.hypot(X0 + c[0] * STEP - T[0],
                  Y0 + c[1] * STEP - T[1]) <= HW + 0.05:
        path = []
        while c is not None:
            path.append((round(X0 + c[0] * STEP, 4),
                         round(Y0 + c[1] * STEP, 4)))
            c = parent[c]
        print(f'REACHED target; path cells {len(path)}')
        print('  path:', list(reversed(path))[::max(1, len(path) // 24)])
        sys.exit(0)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            n = (c[0] + dx, c[1] + dy)
            if n in passable and n not in seen:
                seen.add(n)
                parent[n] = c
                dq.append(n)
print(f'NO PATH: flood {len(seen)} cells')
# name blockers at the frontier midpoint
if seen:
    cx = sum(X0 + c[0] * STEP for c in seen) / len(seen)
    cy = sum(Y0 + c[1] * STEP for c in seen) / len(seen)
    fx = max(seen, key=lambda c: -math.hypot(X0 + c[0] * STEP - T[0],
                                             Y0 + c[1] * STEP - T[1]))
    mx = (X0 + fx[0] * STEP + T[0]) / 2
    my = (Y0 + fx[1] * STEP + T[1]) / 2
    print(f'  frontier centroid ({cx:.2f},{cy:.2f}); closest cell '
          f'({X0 + fx[0] * STEP:.3f},{Y0 + fx[1] * STEP:.3f}); '
          f'midpoint to target ({mx:.2f},{my:.2f})')
    near = []
    for it in pool:
        if it[1] == NET:
            continue
        m, _ = pt_margin(LI, mx, my, NET, 0.0, [it])
        near.append((m, it))
    for m, it in sorted(near)[:6]:
        print(f'    blocker margin {m:+.3f}: {fmt_it(it)}')
