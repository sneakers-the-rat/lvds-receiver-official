"""t_as22: item-model A* for long journeys on exp241esc.
Usage: t_as22.py NET STARTX STARTY GOALRECT(x0,x1,y0,y1) [EXTRA_JSON]
Grid 0.125, 8-dir + via transitions; cell passability = exact pt_margin
(tiled pools); edges need endpoint cells + midpoint pt_margin >= -0.02
(final path is re-gated exactly by the plan gate afterwards).
Prints simplified waypoints per layer + writes scratch/work/as/journey_NET.json.
EXTRA_JSON: optional file with extra obstacle items
[[layer, kind, net, geom...], ...] (the sibling net's emitted copper)."""
import sys, wx, json, heapq, math
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool

NET = sys.argv[1]
SX, SY = float(sys.argv[2]), float(sys.argv[3])
GX0, GX1, GY0, GY1 = map(float, sys.argv[4].split(','))
EXTRA = sys.argv[5] if len(sys.argv) > 5 else None

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = load_items(board)
if EXTRA:
    for (l, kind, net, geom) in json.load(open(EXTRA)):
        if kind == 'via':
            for ll in range(3):
                items[ll].append(('via', net, tuple(geom)))
        else:
            items[l].append(('seg', net, tuple(geom)))

BOX = (66.5, 79.0, 0.5, 27.5)
STEP = 0.125
NX = int((BOX[1] - BOX[0]) / STEP) + 1
NY = int((BOX[3] - BOX[2]) / STEP) + 1

_tile = {}
def pool_for(l, x, y):
    key = (l, int(x // 2.0), int(y // 2.0))
    if key not in _tile:
        cx, cy = key[1] * 2.0, key[2] * 2.0
        sub = in_box_pool(items, (cx - 1.2, cx + 3.2, cy - 1.2, cy + 3.2))
        _tile[key] = sub[l]
    return _tile[key]

def ptm(l, x, y, rad):
    m, _w = pt_margin(l, x, y, NET, rad, pool_for(l, x, y))
    return m

def cell_pt(i, j):
    return (BOX[0] + i * STEP, BOX[2] + j * STEP)

_trk = {}
def trk_ok(l, i, j):
    key = (l, i, j)
    if key not in _trk:
        x, y = cell_pt(i, j)
        _trk[key] = ptm(l, x, y, 0.1) >= 0.0
    return _trk[key]

_via = {}
def via_ok(i, j):
    key = (i, j)
    if key not in _via:
        x, y = cell_pt(i, j)
        _via[key] = all(ptm(l, x, y, 0.25) >= 0.0 for l in range(3))
    return _via[key]

def node_of(x, y):
    return (round((x - BOX[0]) / STEP), round((y - BOX[2]) / STEP))

si, sj = node_of(SX, SY)
def is_goal(i, j):
    x, y = cell_pt(i, j)
    return GX0 - 0.06 <= x <= GX1 + 0.06 and GY0 - 0.06 <= y <= GY1 + 0.06

def heur(i, j):
    x, y = cell_pt(i, j)
    cx = min(max(x, GX0), GX1)
    cy = min(max(y, GY0), GY1)
    return math.hypot(x - cx, y - cy)

start = [(l, si, sj) for l in range(3)]
g_score = {s: 0.0 for s in start}
came = {}
pq = [(heur(si, sj), 0.0, s) for s in start]
heapq.heapify(pq)
goal_node = None
DIRS = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.41421), (1, -1, 1.41421), (-1, 1, 1.41421),
        (-1, -1, 1.41421)]
while pq:
    _f, g, (l, i, j) = heapq.heappop(pq)
    if g > g_score.get((l, i, j), 1e18):
        continue
    if is_goal(i, j):
        goal_node = (l, i, j)
        break
    x, y = cell_pt(i, j)
    # via transitions
    if via_ok(i, j):
        for l2 in range(3):
            if l2 == l:
                continue
            ns = (l2, i, j)
            ng = g + 0.35
            if ng < g_score.get(ns, 1e18):
                g_score[ns] = ng
                came[ns] = (l, i, j)
                heapq.heappush(pq, (ng + heur(i, j), ng, ns))
    for (di, dj, w) in DIRS:
        ni, nj = i + di, j + dj
        if not (0 <= ni < NX and 0 <= nj < NY):
            continue
        if not trk_ok(l, ni, nj):
            continue
        nx_, ny_ = cell_pt(ni, nj)
        mx, my = (x + nx_) / 2, (y + ny_) / 2
        em, _ew = seg_margin(l, (x, y), (nx_, ny_), NET, 0.1,
                             pool_for(l, mx, my), step=0.03)
        if em < -0.001:
            continue
        ns = (l, ni, nj)
        ng = g + w * STEP
        if ng < g_score.get(ns, 1e18):
            g_score[ns] = ng
            came[ns] = (l, i, j)
            heapq.heappush(pq, (ng + heur(ni, nj), ng, ns))

if goal_node is None:
    print(f'{NET}: A* NO PATH; visited {len(g_score)} nodes')
    for l in range(3):
        cells = [(i, j) for (ll, i, j) in g_score if ll == l]
        if cells:
            xs = [cell_pt(i, j)[0] for (i, j) in cells]
            ys = [cell_pt(i, j)[1] for (i, j) in cells]
            print(f'  L{l}: {len(cells)} cells x {min(xs):.2f}..{max(xs):.2f} '
                  f'y {min(ys):.2f}..{max(ys):.2f}')
    sys.exit(1)
path = [goal_node]
while path[-1] in came:
    path.append(came[path[-1]])
path.reverse()
print(f'{NET}: path {len(path)} nodes, cost {g_score[goal_node]:.2f}')
# simplify: split by layer runs, drop collinear points
runs = []
cur = [path[0]]
for n in path[1:]:
    if n[0] != cur[-1][0]:
        runs.append(cur)
        cur = [cur[-1], n]
    else:
        cur.append(n)
runs.append(cur)
out = []
for run in runs:
    l = run[0][0]
    pts = [(round(cell_pt(i, j)[0], 3), round(cell_pt(i, j)[1], 3))
           for (_l, i, j) in run]
    simp = [pts[0]]
    for k in range(1, len(pts) - 1):
        a, b, c = simp[-1], pts[k], pts[k + 1]
        cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(cross) > 1e-9:
            simp.append(b)
    simp.append(pts[-1])
    out.append({'layer': l, 'pts': simp})
    print(f'  L{l}: {simp}')
json.dump(out, open(f'scratch/work/as/journey_{NET}.json', 'w'), indent=1)
print('written', f'scratch/work/as/journey_{NET}.json')
