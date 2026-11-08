"""t_at22: CAP pair 3D A* in the full v7 model.
Pool: t_at20 construction (U9 west 1.0, v6 edits) PLUS winner:
 SCL via (69.35,1.40) r0.25; chord (68.55,2.75)->(68.8,1.9)->
 (69.35,1.40); SDA via (69.4,2.2) r0.25.
Pre-gate of winner copper, then A* both orders (arg).
Usage: t_at22_astar7.py [ORDER]"""
import wx
_app = wx.App(False)
import pcbnew, sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

ORDER = (sys.argv[1] if len(sys.argv) > 1 else 'CAP_CLK,CAP_DATA').split(',')
src = open('scratch/work/at/t_at20_joint2.py').read()
exec(src.split('results = []')[0])
# pool now: v6 edits + U9 west pads + diagonal stub to CHORD0

NEW = []
def add_via_m(net, x, y, r=0.25):
    for li in range(3):
        pool[li].append(('via', net, (x, y, r), netclass(net)[1]))
    NEW.append((-1, ('via', net, (x, y, r), netclass(net)[1])))

def add_seg_m(li, net, a, b, w):
    pool[li].append(('seg', net, (a[0], a[1], b[0], b[1], w / 2),
                     netclass(net)[1]))
    NEW.append((li, ('seg', net, (a[0], a[1], b[0], b[1], w / 2),
                     netclass(net)[1])))

SCL_VIA = (69.35, 1.40)
BEND = (68.8, 1.9)
SDA_VIA = (69.4, 2.2)
add_via_m('I2C_SCL', *SCL_VIA)
add_seg_m(1, 'I2C_SCL', CHORD0, BEND, 0.20)
add_seg_m(1, 'I2C_SCL', BEND, SCL_VIA, 0.20)
add_via_m('I2C_SDA', *SDA_VIA)

def gate_news():
    worst = (9.9, None, None)
    for li, it in NEW:
        cx = it[2][0] if it[0] == 'via' else (it[2][0] + it[2][2]) / 2
        cy = it[2][1] if it[0] == 'via' else (it[2][1] + it[2][3]) / 2
        box = (cx - 2.5, cx + 2.5, cy - 2.5, cy + 2.5)
        local = L.in_box_pool(pool, box, pad=0.6)
        layers = range(3) if li == -1 else [li]
        for l in layers:
            others = [o for lj, o in NEW if (lj == -1 or lj == l)
                      and o is not it and o[1] != it[1]]
            p = local[l] + others
            if it[0] == 'via':
                mm, w = L.pt_margin(l, it[2][0], it[2][1], it[1],
                                    it[2][2], p)
            else:
                dd = it[2]
                mm, w = L.seg_margin(l, (dd[0], dd[1]), (dd[2], dd[3]),
                                     it[1], dd[4], p, step=0.02)
            if mm < worst[0]:
                worst = (mm, it, w)
    return worst

m, it, w = gate_news()
print(f'== pre-gate winner copper: {m:+.3f}  {L.fmt_it(it)} vs '
      f'{L.fmt_it(w)}', flush=True)

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

CASES = {
    'CAP_CLK':  dict(start=(70.15, 1.72), target=(75.45, 25.385)),
    'CAP_DATA': dict(start=(69.90, 3.18), target=(75.45, 22.845)),
}
from scipy import ndimage
sibling_block = {l: np.zeros((NY, NX), dtype=bool) for l in range(3)}

for net in ORDER:
    case = CASES[net]
    G = build_fields(net)
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
    print(f"== {net}: 3D A* goal = {goal is not None}", flush=True)
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
        mm = np.zeros((NY, NX), dtype=bool)
        for (_, iy, ix) in run:
            mm[iy, ix] = True
        sibling_block[l] |= ndimage.binary_dilation(
            mm, structure=np.ones((17, 17)))
    for (vx, vy) in vias:
        vyi, vxi = cell(vx, vy)
        for l in range(3):
            sub = np.zeros((NY, NX), dtype=bool)
            sub[vyi, vxi] = True
            sibling_block[l] |= ndimage.binary_dilation(
                sub, structure=np.ones((29, 29)))
    fn = f"scratch/work/at/journey7_{net}_{''.join(o[4] for o in ORDER)}.json"
    json.dump(out, open(fn, 'w'))
    print(f"   vias: {out['vias']}", flush=True)
    for r in out['runs']:
        print(f"   L{r['layer']}: {len(r['pts'])} pts "
              f"{r['pts'][0]} -> {r['pts'][-1]}", flush=True)
    print(f"   wrote {fn}", flush=True)
