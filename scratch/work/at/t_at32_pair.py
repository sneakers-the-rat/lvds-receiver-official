"""t_as36: 3D A* (layer,cell) per CAP net in its ablated model.
CLK first; DATA second with CLK's resulting cells fenced (same-layer
cells within 0.45 of CLK path blocked; cells within 0.75 of CLK vias
blocked on all layers). Output: densified polylines + via list per net."""
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
import os
ORDER = os.environ.get('ORDER', 'CAP_CLK,CAP_DATA').split(',')

UNION = None
def build_fields(net):
    myclr = netclass(net)[1]
    preds = UNION if UNION is not None else ABL[net]
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
    return G

def cell(x, y):
    return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))

sibling_block = {l: np.zeros((NY, NX), dtype=bool) for l in range(3)}
sibling_vias = []

for ni, net in enumerate(ORDER):
    case = CASES[net]
    if ni > 0:
        UNION = [p for k in ABL for p in ABL[k]]
    G = build_fields(net)
    track = {l: (G[l] >= 0.10) & (~sibling_block[l]) for l in range(3)}
    viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
    for l in range(3):
        viafit &= ~sibling_block[l]
    sc = cell(*case['start'])
    tc = cell(*case['target'])
    def h(p):
        return math.hypot(p[1] - tc[0], p[2] - tc[1])
    start = (1, sc[0], sc[1])  # start on In2 (escape via is through)
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
        # layer moves (via) - cost 6 ~ via penalty
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
                pen = max(0.0, 0.55 - G[l][jy, jx]) * 6.0
                ng = g + step + pen
                q = (l, jy, jx)
                if ng < gs.get(q, 1e18) - 1e-9:
                    gs[q] = ng
                    came[q] = p
                    heapq.heappush(openh, (ng + h(q), ng, q))
    print(f"== {net}: 3D A* goal = {goal is not None}", flush=True)
    if goal is None:
        continue
    path = []
    p = goal
    while p is not None:
        path.append(p)
        p = came[p]
    path.reverse()
    # split into runs + vias
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
    # block sibling cells for the next net
    from scipy import ndimage
    for run in runs:
        l = run[0][0]
        pts = [(float(xs[p[2]]), float(ys[p[1]])) for p in run]
        out['runs'].append(dict(layer=int(l),
                                pts=[[round(a, 3), round(b, 3)]
                                     for a, b in pts]))
        m = np.zeros((NY, NX), dtype=bool)
        for (_, iy, ix) in run:
            m[iy, ix] = True
        dil = ndimage.binary_dilation(m, structure=np.ones((15, 15)))
        sibling_block[l] |= dil
    for (vx, vy) in vias:
        sibling_vias.append((vx, vy))
        vyi, vxi = cell(vx, vy)
        for l in range(3):
            sub = np.zeros((NY, NX), dtype=bool)
            sub[vyi, vxi] = True
            sibling_block[l] |= ndimage.binary_dilation(
                sub, structure=np.ones((27, 27)))
    fn = f"scratch/work/as/journey32_{net}_{''.join(o[4] for o in ORDER)}.json"
    json.dump(out, open(fn, 'w'))
    print(f"   vias: {out['vias']}", flush=True)
    for r in out['runs']:
        print(f"   L{r['layer']}: {len(r['pts'])} pts "
              f"{r['pts'][0]} -> {r['pts'][-1]}", flush=True)
    print(f"   wrote {fn}", flush=True)
