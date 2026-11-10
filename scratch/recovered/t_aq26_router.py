"""t_aq26: exact-model sampled A* router.
Usage: t_aq26_router.py BOARD NET SX SY GX GY X0 X1 Y0 Y1 [EXTRA_ADDS_JSON]
Nodes: 0.25-grid points per layer where a w0.2 track centreline fits
(pt_margin rad 0.1 >= 0.005); via transitions only where a d0.5 via
fits on all layers (pt_margin rad 0.25 >= 0.005). Edges: 8-neighbour
grid steps gated by seg_margin (step 0.05). A* + greedy shortcut
simplification. EXTRA_ADDS_JSON: [[net,li,ax,ay,bx,by,w],...] static
segs added before routing (e.g. a sibling journey already routed).
Prints the simplified path as JSON lines."""
import sys, wx, json, math, heapq
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool

BOARD, NET = sys.argv[1], sys.argv[2]
SX, SY, GX, GY = map(float, sys.argv[3:7])
X0, X1, Y0, Y1 = map(float, sys.argv[7:11])
EXTRA = json.loads(sys.argv[11]) if len(sys.argv) > 11 else []
GRID = 0.25
VIA_COST = 4.0

board = pcbnew.LoadBoard(BOARD)
items = load_items(board)
statics = {l: list(items[l]) for l in range(3)}
for (n, li, ax, ay, bx, by, w) in EXTRA:
    statics[li].append(('seg', n, (ax, ay, bx, by, w / 2), 0.2))

def pool_for(li, a, b):
    box = (min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]))
    return in_box_pool(statics, box, pad=0.7)[li]

def seg_ok(li, a, b):
    p = pool_for(li, a, b)
    m, _w = seg_margin(li, a, b, NET, 0.1, p, step=0.05)
    return m >= -0.001

def pt_ok(li, x, y, rad):
    box = (x - 0.8, x + 0.8, y - 0.8, y + 0.8)
    p = in_box_pool(statics, box, pad=0.7)[li]
    m, _w = pt_margin(li, x, y, NET, rad, p)
    return m >= 0.005

nx = int(round((X1 - X0) / GRID)) + 1
ny = int(round((Y1 - Y0) / GRID)) + 1
def cxy(i, j):
    return (X0 + i * GRID, Y0 + j * GRID)

trk = [[[False] * ny for _ in range(nx)] for _ in range(3)]
viaok = [[False] * ny for _ in range(nx)]
for i in range(nx):
    for j in range(ny):
        x, y = cxy(i, j)
        for li in range(3):
            trk[li][i][j] = pt_ok(li, x, y, 0.1)
        viaok[i][j] = all(pt_ok(li, x, y, 0.25) for li in range(3))
print(f'grid {nx}x{ny}; trk cells '
      f'{[sum(sum(r) for r in trk[l]) for l in range(3)]}; '
      f'via cells {sum(sum(r) for r in viaok)}', file=sys.stderr)

def nearest_free(x, y):
    bi = min(range(nx), key=lambda i: abs(X0 + i * GRID - x))
    bj = min(range(ny), key=lambda j: abs(Y0 + j * GRID - y))
    return bi, bj

# nodes: (i, j, li); start/goal attach to their exact points via
# virtual nodes (-1) handled by seeding distances over nearby cells.
si, sj = nearest_free(SX, SY)
gi, gj = nearest_free(GX, GY)
starts = []
for i in range(max(0, si - 2), min(nx, si + 3)):
    for j in range(max(0, sj - 2), min(ny, sj + 3)):
        x, y = cxy(i, j)
        for li in range(3):
            if trk[li][i][j] and seg_ok(li, (SX, SY), (x, y)):
                starts.append((i, j, li))
goals = set()
for i in range(max(0, gi - 2), min(nx, gi + 3)):
    for j in range(max(0, gj - 2), min(ny, gj + 3)):
        x, y = cxy(i, j)
        for li in range(3):
            if trk[li][i][j] and seg_ok(li, (x, y), (GX, GY)):
                goals.add((i, j, li))
print(f'starts {len(starts)} goals {len(goals)}', file=sys.stderr)
assert starts and goals, 'no start/goal attachment'

def heur(i, j):
    x, y = cxy(i, j)
    return math.hypot(x - GX, y - GY)

gs = {}
came = {}
open_h = []
for s in starts:
    gs[s] = 0.0; came[s] = None
    heapq.heappush(open_h, (heur(s[0], s[1]), 0.0, s))
found = None
while open_h:
    f, g, cur = heapq.heappop(open_h)
    if cur in goals:
        found = cur; break
    if g > gs.get(cur, 1e18):
        continue
    i, j, li = cur
    x, y = cxy(i, j)
    if viaok[i][j]:
        for nl in range(3):
            if nl == li:
                continue
            nb = (i, j, nl)
            ng = g + VIA_COST
            if ng < gs.get(nb, 1e18):
                gs[nb] = ng; came[nb] = cur
                heapq.heappush(open_h, (ng + heur(i, j), ng, nb))
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ni, nj = i + di, j + dj
            if not (0 <= ni < nx and 0 <= nj < ny):
                continue
            if not trk[li][ni][nj]:
                continue
            if di and dj and not (trk[li][i][nj] and trk[li][ni][j]):
                continue
            a = (x, y); b = cxy(ni, nj)
            if not seg_ok(li, a, b):
                continue
            nb = (ni, nj, li)
            ng = g + GRID * (1.41421 if di and dj else 1.0)
            if ng < gs.get(nb, 1e18):
                gs[nb] = ng; came[nb] = cur
                heapq.heappush(open_h, (ng + heur(ni, nj), ng, nb))
assert found, 'NO PATH'
path = []
cur = found
while cur:
    path.append(cur); cur = came[cur]
path.reverse()
# materialize: [(li, x, y)...] with start/goal exact points
pts = [(path[0][2], SX, SY)]
for (i, j, li) in path:
    x, y = cxy(i, j)
    if (x, y) != (pts[-1][1], pts[-1][2]):
        pts.append((li, x, y))
pts.append((path[-1][2], GX, GY))
print(f'raw path {len(pts)} pts, cost {gs[found]:.1f}', file=sys.stderr)

# greedy shortcut per layer-run
def simplify(pts):
    out = [pts[0]]
    idx = 0
    while idx < len(pts) - 1:
        li = pts[idx][0]
        best = idx + 1
        for k in range(len(pts) - 1, idx + 1, -1):
            if pts[k][0] != li:
                continue
            if seg_ok(li, (pts[idx][1], pts[idx][2]),
                      (pts[k][1], pts[k][2])):
                best = k
                break
        out.append(pts[best])
        idx = best
    return out

simp = simplify(pts)
print(f'simplified {len(simp)} pts', file=sys.stderr)
# emit as seg/via plan
plan = []
for a, b in zip(simp, simp[1:]):
    if a[0] == b[0]:
        if (a[1], a[2]) != (b[1], b[2]):
            plan.append(('seg', NET, a[0], a[1], a[2], b[1], b[2], 0.2))
    else:
        plan.append(('via', NET, a[1], a[2]))
        if (a[1], a[2]) != (b[1], b[2]):
            plan.append(('seg', NET, b[0], b[1], b[2], a[1], a[2], 0.2))
print(json.dumps(plan))
