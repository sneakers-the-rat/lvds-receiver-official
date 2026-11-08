"""t_at26: DATA widest with CLK's CD journey as fences, pair model:
esc items minus band ablation (x<70.2,y<7) minus XO web minus
+3V3D web; CLK journey densified into seg/via fence items."""
import wx
_app = wx.App(False)
import pcbnew, sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)

def centre(it):
    d = it[2]
    if it[0] == 'seg':
        return ((d[0] + d[2]) / 2, (d[1] + d[3]) / 2)
    return (d[0], d[1])

pool = {0: [], 1: [], 2: []}
for li in range(3):
    for it in items[li]:
        cx, cy = centre(it)
        if li == 1 and it[1] == 'HV_SHDN' and cx < 70.2 and cy < 7:
            continue
        if li == 1 and it[1] == 'XO' and 66 < cx < 76 and 16 < cy < 23:
            continue
        if li == 0 and it[1] == '+3V3D' and 70 < cx < 76 and 20 < cy < 26:
            continue
        pool[li].append(it)

# CLK journey as fences
J = json.load(open('scratch/work/as/journey_CAP_CLK_CD.json'))
for (vx, vy) in J['vias']:
    for li in range(3):
        pool[li].append(('via', 'CAP_CLK', (vx, vy, 0.25), 0.2))
for run in J['runs']:
    pts = run['pts']
    for a, b in zip(pts, pts[1:]):
        pool[run['layer']].append(
            ('seg', 'CAP_CLK', (a[0], a[1], b[0], b[1], 0.10), 0.2))

X0, X1, Y0, Y1, ST = 63.0, 79.5, -3.0, 29.5, 0.05
xs = np.arange(X0, X1 + 1e-9, ST)
ys = np.arange(Y0, Y1 + 1e-9, ST)
GX, GY = np.meshgrid(xs, ys)
NY, NX = GX.shape

def item_dist_field(it):
    kind, dd = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = dd
        dx, dy = GX - cx, GY - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = dd
        px, py = GX - x1, GY - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    cx, cy, r = dd
    return np.hypot(GX - cx, GY - cy) - r

def item_bbox(it):
    kind, dd = it[0], it[2]
    if kind == 'pad':
        r = math.hypot(dd[2], dd[3])
        return dd[0] - r, dd[0] + r, dd[1] - r, dd[1] + r
    if kind == 'seg':
        return (min(dd[0], dd[2]) - dd[4], max(dd[0], dd[2]) + dd[4],
                min(dd[1], dd[3]) - dd[4], max(dd[1], dd[3]) + dd[4])
    return dd[0] - dd[2], dd[0] + dd[2], dd[1] - dd[2], dd[1] + dd[2]

def build_fields(net):
    myclr = netclass(net)[1]
    G = {}
    for l in range(3):
        field = np.full(GX.shape, 9.9)
        for it in pool[l]:
            if it[1] == net:
                continue
            bx0, bx1, by0, by1 = item_bbox(it)
            req = max(myclr, it[3])
            if bx1 < X0 - req - 0.3 or bx0 > X1 + req + 0.3 or \
               by1 < Y0 - req - 0.3 or by0 > Y1 + req + 0.3:
                continue
            field = np.minimum(field, item_dist_field(it) - req)
        G[l] = field
    return G

def cell(x, y):
    return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))

net = 'CAP_DATA'
case = dict(start=(69.90, 3.18), target=(75.45, 22.845))
G = build_fields(net)
sc = cell(*case['start'])
tc = cell(*case['target'])
INF = float('inf')
best = {}
pq = []
start_state = (1, sc[0], sc[1])
v0 = min(G[1][sc], 9.9)
best[start_state] = v0
heapq.heappush(pq, (-v0, start_state))
came = {start_state: None}
while pq:
    negv, p = heapq.heappop(pq)
    v = -negv
    if v < best.get(p, -INF) - 1e-9:
        continue
    l, iy, ix = p
    if l == 0 and (iy, ix) == tc:
        break
    cand = []
    for l2 in range(3):
        if l2 != l:
            cand.append(((l2, iy, ix),
                         min(G[0][iy, ix], G[1][iy, ix], G[2][iy, ix])
                         - 0.25))
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            jy, jx = iy + dy, ix + dx
            if 0 <= jy < NY and 0 <= jx < NX:
                cand.append(((l, jy, jx), G[l][jy, jx] - 0.10))
    for q, w in cand:
        nv = min(v, w)
        if nv > best.get(q, -INF) + 1e-9:
            best[q] = nv
            came[q] = p
            heapq.heappush(pq, (-nv, q))
goal = (0, tc[0], tc[1])
bval = best.get(goal, -INF)
print(f'== {net} vs CLK journey: widest bottleneck = {bval:+.3f}',
      flush=True)
path = []
p = goal
while p is not None:
    path.append(p)
    p = came.get(p)
path.reverse()
seen = set()
for p, q in zip(path, path[1:]):
    if q[0] != p[0]:
        v = min(G[0][p[1], p[2]], G[1][p[1], p[2]], G[2][p[1], p[2]]) - 0.25
        kind = 'viafit'
        cellq = p
    else:
        v = G[q[0]][q[1], q[2]] - 0.10
        kind = 'track'
        cellq = q
    if v <= bval + 0.004:
        l, iy, ix = cellq
        x, y = float(xs[ix]), float(ys[iy])
        box = (x - 2.2, x + 2.2, y - 2.2, y + 2.2)
        local = L.in_box_pool(pool, box, pad=0.6)
        mm, w = L.pt_margin(l, x, y, net, 0.10, local[l])
        key = L.fmt_it(w)
        if key in seen:
            continue
        seen.add(key)
        print(f'   bind L{l} ({x:.2f},{y:.2f}) {kind} {v:+.3f} '
              f'vs {key}', flush=True)
