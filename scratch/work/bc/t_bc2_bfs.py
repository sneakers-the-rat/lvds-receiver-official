"""t_bc2: multi-layer Dijkstra (groute grid model, 0.125) for the XI ride
on exp256, seeded from the west fragment's OWN copper cells and goaled at
the pocket fragment's own copper cells (PV disc + F leg + U7.28 pad).
Existing vias bridge layers through their copper cells, so the model
never has to place a via inside the pocket district. Layer changes at
via_ok cells are allowed at cost 3 (new vias), plain steps cost 1
(diag 1.414). Emits the raw waypoint path as JSON + a layer-run summary.
"""
import heapq, json, math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

NET = 'XI'
SRC = 'hw/pdlvds_rx.exp256.kicad_pcb'
CELL = 0.125
TRK_HW = 0.1
VIA_R = 0.25
EPS = 0.004
X0, X1, Y0, Y1 = 66.0, 92.0, 2.0, 26.0
NX = int(round((X1 - X0) / CELL)) + 1
NY = int(round((Y1 - Y0) / CELL)) + 1

board = pcbnew.LoadBoard(SRC)
items, _pc = repair.build_items(board)

def pair_clr(n, other):
    return max(netclass(n)[1], netclass(other)[1] if other else 0.2)

def pt_clear(li, x, y, rad):
    seen = set()
    for it in items[li].near(li, x, y):
        if it[1] == NET or id(it) in seen:
            continue
        seen.add(id(it))
        if dist_to_item(it, x, y) < rad + pair_clr(NET, it[1]) + EPS:
            return False
    return True

def cxy(i, j):
    return (X0 + i * CELL, Y0 + j * CELL)

print('building trk_ok grids...', flush=True)
trk_ok = [[[False] * NY for _ in range(NX)] for _ in range(3)]
for i in range(NX):
    for j in range(NY):
        x, y = cxy(i, j)
        for li in range(3):
            trk_ok[li][i][j] = pt_clear(li, x, y, TRK_HW)

via_cache = {}
def via_ok(i, j):
    if (i, j) not in via_cache:
        x, y = cxy(i, j)
        via_cache[(i, j)] = all(pt_clear(li, x, y, VIA_R) for li in range(3))
    return via_cache[(i, j)]

# --- fragment copper cells -------------------------------------------------
def item_point(it):
    k = it[0]
    if k == 'pad':
        return (it[2][0], it[2][1])
    if k == 'via':
        return (it[2][0], it[2][1])
    return ((it[2][0] + it[2][2]) / 2, (it[2][1] + it[2][3]) / 2)

def item_bbox(it):
    k = it[0]
    if k == 'pad':
        cx, cy, hw, hh, _r = it[2]
        return (cx - hw - 0.2, cy - hh - 0.2, cx + hw + 0.2, cy + hh + 0.2)
    if k == 'via':
        cx, cy, r = it[2]
        return (cx - r - 0.2, cy - r - 0.2, cx + r + 0.2, cy + r + 0.2)
    x1, y1, x2, y2, hw = it[2]
    return (min(x1, x2) - hw - 0.2, min(y1, y2) - hw - 0.2,
            max(x1, x2) + hw + 0.2, max(y1, y2) + hw + 0.2)

def is_pocket(it):
    x, y = item_point(it)
    return 75.4 <= x <= 76.7 and 9.8 <= y <= 12.1

west_cells, pocket_cells = set(), set()
for li in range(3):
    seen = set()
    all_items = []
    for key, lst in items[li].buckets.items():
        if key[0] == li:
            all_items.extend(lst)
    for it in all_items:
        if it[1] != NET or id(it) in seen:
            continue
        seen.add(id(it))
        tgt = pocket_cells if is_pocket(it) else west_cells
        bx = item_bbox(it)
        i0 = max(0, int((bx[0] - X0) / CELL)); i1 = min(NX - 1, int((bx[2] - X0) / CELL) + 1)
        j0 = max(0, int((bx[1] - Y0) / CELL)); j1 = min(NY - 1, int((bx[3] - Y0) / CELL) + 1)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                x, y = cxy(i, j)
                if dist_to_item(it, x, y) <= 0.05:
                    tgt.add((i, j, li))
print(f'west copper cells: {len(west_cells)}, pocket copper cells: {len(pocket_cells)}', flush=True)
for c in sorted(pocket_cells):
    print('  pocket cell', c, cxy(c[0], c[1]), 'layer', c[2])

# --- Dijkstra ---------------------------------------------------------------
INF = float('inf')
dist = {}
parent = {}
pq = []
for c in west_cells:
    dist[c] = 0.0
    pq.append((0.0, c))
heapq.heapify(pq)
goal = None
while pq:
    d, u = heapq.heappop(pq)
    if d > dist.get(u, INF):
        continue
    if u in pocket_cells:
        goal = u
        break
    i, j, li = u
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ni, nj = i + di, j + dj
            if not (0 <= ni < NX and 0 <= nj < NY):
                continue
            v = (ni, nj, li)
            if v not in west_cells and v not in pocket_cells:
                if not trk_ok[li][ni][nj]:
                    continue
                if di and dj and not (trk_ok[li][i][nj] and trk_ok[li][ni][j]):
                    continue  # corner-cut prevention
            w = 1.414 if (di and dj) else 1.0
            nd = d + w
            if nd < dist.get(v, INF):
                dist[v] = nd
                parent[v] = u
                heapq.heappush(pq, (nd, v))
    for li2 in range(3):
        if li2 == li:
            continue
        v = (i, j, li2)
        if v in west_cells or v in pocket_cells or via_ok(i, j):
            nd = d + 3.0
            if nd < dist.get(v, INF):
                dist[v] = nd
                parent[v] = u
                heapq.heappush(pq, (nd, v))

if goal is None:
    print('NO PATH in model (with existing-copper bridges + via_ok transitions)')
    sys.exit(1)

path = []
u = goal
while u is not None:
    path.append(u)
    u = parent.get(u)
path.reverse()
pts = [(cxy(i, j)[0], cxy(i, j)[1], li) for (i, j, li) in path]
print(f'PATH cells: {len(pts)} cost={dist[goal]:.1f}')
runs = []
for p in pts:
    if runs and runs[-1][2] == p[2]:
        runs[-1][1] = p
        runs[-1][3] += 1
    else:
        runs.append([p, p, p[2], 1])
for a, b_, li, n in runs:
    print(f'  layer {li} run {n} cells: ({a[0]:.3f},{a[1]:.3f}) -> ({b_[0]:.3f},{b_[1]:.3f})')
json.dump(pts, open('scratch/work/bc/xi_bfs_path.json', 'w'))
print('saved scratch/work/bc/xi_bfs_path.json')
