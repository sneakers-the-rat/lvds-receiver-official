"""t_as35: extract concrete cell paths for the CAP nets in their ablated
models (from t_as34): component sequence + one via cell per transition,
then per-layer A* between anchor cells, simplified to waypoint runs.
Output: JSON per net with [(layer, [(x,y)...]), ...] and via points."""
import wx
_app = wx.App(False)
import pcbnew, sys, math, json, heapq
import numpy as np
from scipy import ndimage
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass
from collections import deque

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)
X0, X1, Y0, Y1, ST = 63.0, 79.5, -3.0, 29.5, 0.05
xs = np.arange(X0, X1 + 1e-9, ST)
ys = np.arange(Y0, Y1 + 1e-9, ST)
GX, GY = np.meshgrid(xs, ys)
NY, NX = GX.shape

def item_dist_field(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = GX - cx, GY - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = GX - x1, GY - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    cx, cy, r = d
    return np.hypot(GX - cx, GY - cy) - r

def item_bbox(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        r = math.hypot(d[2], d[3])
        return d[0] - r, d[0] + r, d[1] - r, d[1] + r
    if kind == 'seg':
        return (min(d[0], d[2]) - d[4], max(d[0], d[2]) + d[4],
                min(d[1], d[3]) - d[4], max(d[1], d[3]) + d[4])
    return d[0] - d[2], d[0] + d[2], d[1] - d[2], d[1] + d[2]

def item_centre(it):
    d = it[2]
    if it[0] == 'seg':
        return ((d[0] + d[2]) / 2, (d[1] + d[3]) / 2)
    return (d[0], d[1])

ABL = {
    'CAP_CLK': [
        lambda l, it: l == 1 and it[1] == 'HV_SHDN'
            and item_centre(it)[0] < 70.2 and item_centre(it)[1] < 7,
        lambda l, it: l == 0 and it[1] == '+3V3D'
            and 70 < item_centre(it)[0] < 76 and 20 < item_centre(it)[1] < 26,
    ],
    'CAP_DATA': [
        lambda l, it: l == 1 and it[1] == 'XO'
            and 66 < item_centre(it)[0] < 76 and 16 < item_centre(it)[1] < 23,
        lambda l, it: l == 1 and it[1] == 'HV_SHDN'
            and item_centre(it)[0] < 70.2 and item_centre(it)[1] < 7,
    ],
}
CASES = {
    'CAP_CLK':  dict(start=(70.02, 1.83), target=(75.45, 25.385)),
    'CAP_DATA': dict(start=(69.90, 3.18), target=(75.45, 22.845)),
}

def simplify(cells, tol=0.09):
    """cells: list of (x,y). Greedy: keep farthest point within tol of the
    line from the anchor (Ramer-like, simple forward scan)."""
    if len(cells) <= 2:
        return cells
    out = [cells[0]]
    anchor = cells[0]
    prev = cells[1]
    for p in cells[2:]:
        # distance of prev from line anchor->p
        ax, ay = anchor
        px, py = p
        vx, vy = prev
        dx, dy = px - ax, py - ay
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((vx - ax) * dx + (vy - ay) * dy) / L2))
        d = math.hypot(vx - (ax + t * dx), vy - (ay + t * dy))
        if d > tol:
            out.append(prev)
            anchor = prev
        prev = p
    out.append(cells[-1])
    return out

def astar(track_l, g_l, a, b):
    """A* on cells of one layer; a,b = (iy,ix). Cost: step + proximity
    penalty pulling toward high-G (channel centre)."""
    def h(p):
        return math.hypot(p[0] - b[0], p[1] - b[1])
    openh = [(h(a), 0.0, a)]
    came = {a: None}
    gs = {a: 0.0}
    while openh:
        _, g, p = heapq.heappop(openh)
        if p == b:
            path = []
            while p is not None:
                path.append(p)
                p = came[p]
            return path[::-1]
        if g > gs.get(p, 1e18) + 1e-9:
            continue
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                q = (p[0] + dy, p[1] + dx)
                if not (0 <= q[0] < NY and 0 <= q[1] < NX):
                    continue
                if not track_l[q]:
                    continue
                step = 1.414 if dx and dy else 1.0
                pen = max(0.0, 0.35 - g_l[q]) * 1.2
                ng = g + step + pen
                if ng < gs.get(q, 1e18) - 1e-9:
                    gs[q] = ng
                    came[q] = p
                    heapq.heappush(openh, (ng + h(q), ng, q))
    return None

for net, case in CASES.items():
    myclr = netclass(net)[1]
    preds = ABL[net]
    G = {}
    for l in range(3):
        field = np.full(GX.shape, 9.9)
        for it in items[l]:
            if it[1] == net or any(p(l, it) for p in preds):
                continue
            bx0, bx1, by0, by1 = item_bbox(it)
            req = max(myclr, it[3])
            if bx1 < X0 - req - 0.3 or bx0 > X1 + req + 0.3 or \
               by1 < Y0 - req - 0.3 or by0 > Y1 + req + 0.3:
                continue
            field = np.minimum(field, item_dist_field(it) - req)
        G[l] = field
    track = {l: G[l] >= 0.10 for l in range(3)}
    viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
    comp = {l: ndimage.label(track[l], structure=np.ones((3, 3)))[0]
            for l in range(3)}
    def cell(x, y):
        return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))
    startc = cell(*case['start'])
    targetc = cell(*case['target'])
    # adjacency with one via cell kept per comp pair
    adj = {}
    for (cy, cx) in np.argwhere(viafit):
        ls = [l for l in range(3) if track[l][cy, cx]]
        for i in range(len(ls)):
            for j in range(i + 1, len(ls)):
                a = (ls[i], int(comp[ls[i]][cy, cx]))
                b = (ls[j], int(comp[ls[j]][cy, cx]))
                if b not in adj.setdefault(a, {}):
                    adj[a][b] = (int(cy), int(cx))
                if a not in adj.setdefault(b, {}):
                    adj[b][a] = (int(cy), int(cx))
    # BFS comp graph
    prev = {}
    dq = deque()
    for l in range(3):
        if track[l][startc]:
            n = (l, int(comp[l][startc]))
            prev[n] = (None, startc)
            dq.append(n)
    target_node = (0, int(comp[0][targetc]))
    found = False
    while dq:
        n = dq.popleft()
        if n == target_node:
            found = True
            break
        for m, vc in adj.get(n, {}).items():
            if m not in prev:
                prev[m] = (n, vc)
                dq.append(m)
    print(f"== {net}: comp path found = {found}", flush=True)
    if not found:
        continue
    # reconstruct: sequence of (layer, entry cell, exit cell)
    chain = []
    n = target_node
    while n is not None:
        pn, vc = prev[n]
        chain.append((n, vc))
        n = pn
    chain.reverse()
    # chain[i] = (node, via cell used to ENTER node) ; first entry = start
    runs = []
    for i, (node, vc) in enumerate(chain):
        l = node[0]
        entry = vc if i > 0 else startc
        if i + 1 < len(chain):
            exitc = chain[i + 1][1]
        else:
            exitc = targetc
        runs.append((l, entry, exitc))
    result = []
    for (l, a, b) in runs:
        cells = astar(track[l], G[l], a, b)
        if cells is None:
            print(f"   A* FAILED on layer {l} {a}->{b}", flush=True)
            result = None
            break
        pts = [(round(float(xs[cx]), 3), round(float(ys[cy]), 3))
               for (cy, cx) in cells]
        simp = simplify(pts)
        result.append(dict(layer=l, entry=[round(float(xs[a[1]]), 3),
                                          round(float(ys[a[0]]), 3)],
                           exit=[round(float(xs[b[1]]), 3),
                                 round(float(ys[b[0]]), 3)],
                           waypoints=simp))
        print(f"   L{l}: {len(pts)} cells -> {len(simp)} waypoints", flush=True)
    if result:
        fn = f"scratch/work/as/path_{net}.json"
        json.dump(result, open(fn, 'w'), indent=1)
        print(f"   wrote {fn}", flush=True)
        for r in result:
            print(f"   L{r['layer']} entry {r['entry']} exit {r['exit']}")
            print(f"      {r['waypoints']}")
