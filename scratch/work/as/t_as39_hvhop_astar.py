"""t_as39: A* both CAP nets in a model where HV_SHDN's staircase has a
7-seg rip window (band points (67.375,2.125)..(65.625,3.875)) and the
HV B-hop (vias (67.6,1.95),(65.4,4.15); B segs between) is present as a
foreign fence. Also ablated: +3V3D F web U5 (CLK arrival), XO In2 web
(DATA arrival) - the fence re-lays for those are designed separately.
Sibling fencing exact radii (0.4 track / 0.7 via)."""
import wx
_app = wx.App(False)
import pcbnew, sys, math, json, heapq
import numpy as np
from scipy import ndimage
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass, dist_to_item

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)
X0, X1, Y0, Y1, ST = 63.0, 79.5, -3.0, 29.5, 0.05
xs = np.arange(X0, X1 + 1e-9, ST)
ys = np.arange(Y0, Y1 + 1e-9, ST)
GX, GY = np.meshgrid(xs, ys)
NY, NX = GX.shape

RIP_SEGS = {  # (x1,y1,x2,y2) on In2, HV_SHDN
    (67.375, 2.125, 67.125, 2.375), (67.125, 2.375, 66.875, 2.625),
    (66.875, 2.625, 66.625, 2.875), (66.625, 2.875, 66.375, 3.125),
    (66.375, 3.125, 66.125, 3.375), (66.125, 3.375, 65.875, 3.625),
    (65.875, 3.625, 65.625, 3.875),
}
def is_rip(l, it):
    if l != 1 or it[1] != 'HV_SHDN' or it[0] != 'seg':
        return False
    d = it[2]
    key = (round(d[0], 3), round(d[1], 3), round(d[2], 3), round(d[3], 3))
    rkey = (key[2], key[3], key[0], key[1])
    return key in RIP_SEGS or rkey in RIP_SEGS

HOP_ITEMS = {0: [], 1: [], 2: []}
for l in range(3):
    HOP_ITEMS[l].append(('via', 'HV_SHDN', (67.6, 1.95, 0.25), 0.2))
    HOP_ITEMS[l].append(('via', 'HV_SHDN', (65.4, 4.15, 0.25), 0.2))
HOP_ITEMS[2].append(('seg', 'HV_SHDN', (67.6, 1.95, 66.6, 2.9, 0.125), 0.2))
HOP_ITEMS[2].append(('seg', 'HV_SHDN', (66.6, 2.9, 65.4, 4.15, 0.125), 0.2))
HOP_ITEMS[1].append(('seg', 'HV_SHDN', (67.375, 2.125, 67.6, 1.95, 0.125), 0.2))
HOP_ITEMS[1].append(('seg', 'HV_SHDN', (65.4, 4.15, 65.625, 3.875, 0.125), 0.2))

def item_centre(it):
    d = it[2]
    if it[0] == 'seg':
        return ((d[0] + d[2]) / 2, (d[1] + d[3]) / 2)
    return (d[0], d[1])

EXTRA_ABL = {
    'CAP_CLK': [lambda l, it: l == 0 and it[1] == '+3V3D'
                and 70 < item_centre(it)[0] < 76
                and 20 < item_centre(it)[1] < 26],
    'CAP_DATA': [lambda l, it: l == 1 and it[1] == 'XO'
                 and 66 < item_centre(it)[0] < 76
                 and 16 < item_centre(it)[1] < 23],
}
CASES = {
    'CAP_CLK':  dict(start=(70.02, 1.83), target=(75.45, 25.385)),
    'CAP_DATA': dict(start=(69.90, 3.18), target=(75.45, 22.845)),
}

def dist_field(it, GX, GY):
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

def cell(x, y):
    return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))

sibling_block = {l: np.zeros((NY, NX), dtype=bool) for l in range(3)}

for net in ('CAP_CLK', 'CAP_DATA'):
    case = CASES[net]
    myclr = netclass(net)[1]
    preds = EXTRA_ABL[net]
    G = {}
    for l in range(3):
        field = np.full(GX.shape, 9.9)
        pool = [it for it in items[l]
                if it[1] != net and not is_rip(l, it)
                and not any(p(l, it) for p in preds)] + HOP_ITEMS[l]
        for it in pool:
            bx0, bx1, by0, by1 = item_bbox(it)
            req = max(myclr, it[3])
            if bx1 < X0 - req - 0.3 or bx0 > X1 + req + 0.3 or \
               by1 < Y0 - req - 0.3 or by0 > Y1 + req + 0.3:
                continue
            field = np.minimum(field, dist_field(it, GX, GY) - req)
        G[l] = field
    track = {l: (G[l] >= 0.10) & (~sibling_block[l]) for l in range(3)}
    viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
    for l in range(3):
        viafit &= ~sibling_block[l]
    sc = cell(*case['start'])
    tc = cell(*case['target'])
    def h(p):
        return math.hypot(p[1] - tc[0], p[2] - tc[1])
    start = (1, sc[0], sc[1])
    openh = [(h(start), 0.0, start)]
    came = {start: None}
    gs = {start: 0.0}
    goal = None
    while openh:
        _, g, p = heapq.heappop(openh)
        if g > gs.get(p, 1e18) + 1e-9:
            continue
        l, iy, ix = p
        if l == 0 and (iy, ix) == tc:
            goal = p
            break
        for l2 in range(3):
            if l2 != l and viafit[iy, ix] and track[l2][iy, ix]:
                q = (l2, iy, ix)
                ng = g + 6.0
                if ng < gs.get(q, 1e18) - 1e-9:
                    gs[q] = ng
                    came[q] = p
                    heapq.heappush(openh, (ng + h(q), ng, q))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                jy, jx = iy + dy, ix + dx
                if not (0 <= jy < NY and 0 <= jx < NX):
                    continue
                if not track[l][jy, jx]:
                    continue
                step = 1.414 if dx and dy else 1.0
                pen = max(0.0, 0.35 - G[l][jy, jx]) * 1.5
                ng = g + step + pen
                q = (l, jy, jx)
                if ng < gs.get(q, 1e18) - 1e-9:
                    gs[q] = ng
                    came[q] = p
                    heapq.heappush(openh, (ng + h(q), ng, q))
    print(f"== {net}: goal = {goal is not None}", flush=True)
    if goal is None:
        continue
    path = []
    p = goal
    while p is not None:
        path.append(p)
        p = came[p]
    path.reverse()
    runs = []
    vias = []
    cur = [path[0]]
    for p in path[1:]:
        if p[0] == cur[-1][0]:
            cur.append(p)
        else:
            runs.append(cur)
            vias.append((float(xs[cur[-1][2]]), float(ys[cur[-1][1]])))
            cur = [p]
    runs.append(cur)
    out = dict(net=net, vias=[[round(a, 3), round(b, 3)] for a, b in vias],
               runs=[])
    for run in runs:
        l = run[0][0]
        pts = [(float(xs[p[2]]), float(ys[p[1]])) for p in run]
        out['runs'].append(dict(layer=int(l),
                                pts=[[round(a, 3), round(b, 3)]
                                     for a, b in pts]))
        m = np.zeros((NY, NX), dtype=bool)
        for (_, iy, ix) in run:
            m[iy, ix] = True
        sibling_block[l] |= ndimage.binary_dilation(
            m, structure=np.ones((17, 17)))
    for (vx, vy) in vias:
        vyi, vxi = cell(vx, vy)
        for l in range(3):
            sub = np.zeros((NY, NX), dtype=bool)
            sub[vyi, vxi] = True
            sibling_block[l] |= ndimage.binary_dilation(
                sub, structure=np.ones((29, 29)))
    fn = f"scratch/work/as/journey2_{net}.json"
    json.dump(out, open(fn, 'w'))
    print(f"   vias: {out['vias']}", flush=True)
    for r in out['runs']:
        print(f"   L{r['layer']}: {len(r['pts'])} pts "
              f"{r['pts'][0]} -> {r['pts'][-1]}", flush=True)
