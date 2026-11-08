"""t_at3: pair 3D A* for CAP_CLK/CAP_DATA in the gap-opened model.
Model = exp241esc items minus removals (HV band 4+7, SDA via+B stub+
vertical, GND F tree) plus fixed new copper (HV mouth hop + band hop,
SDA via S + B re-lay diagonal). Flexible heals (SDA staircase, SCL B,
+3V3A F, GND tree) absent - they route later in leftover space.
Usage: t_at3_astar.py sx sy ex ey [ORDER]  (ORDER like CAP_CLK,CAP_DATA)
Writes journey JSONs to scratch/work/at/."""
import wx
_app = wx.App(False)
import pcbnew, sys, math, json, heapq, os
import numpy as np
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

SX, SY, EX, EY = (float(a) for a in sys.argv[1:5])
ORDER = (sys.argv[5] if len(sys.argv) > 5 else 'CAP_CLK,CAP_DATA').split(',')
W = (68.05, 0.20)
BW1, BW2 = (67.6, 1.95), (65.4, 4.15)

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)

def key_seg(d):
    a = (round(d[0], 3), round(d[1], 3), round(d[2], 3), round(d[3], 3))
    b = (round(d[2], 3), round(d[3], 3), round(d[0], 3), round(d[1], 3))
    return a, b

REM_SEGS = {
    1: [('HV_SHDN', s) for s in [
        (68.875, 0.625, 69.125, 0.375), (69.125, 0.375, 69.375, 0.125),
        (69.375, 0.125, 69.625, -0.125), (69.625, -0.125, 69.875, -0.375),
        (67.375, 2.125, 67.125, 2.375), (67.125, 2.375, 66.875, 2.625),
        (66.875, 2.625, 66.625, 2.875), (66.625, 2.875, 66.375, 3.125),
        (66.375, 3.125, 66.125, 3.375), (66.125, 3.375, 65.875, 3.625),
        (65.875, 3.625, 65.625, 3.875)]],
    2: [('I2C_SDA', s) for s in [
        (69.900, 0.820, 69.875, 0.625), (69.875, 0.625, 69.875, -9.125)]],
    0: [('GND', s) for s in [
        (71.000, 0.270, 69.600, 0.250), (69.600, 0.250, 68.900, 0.850),
        (68.900, 0.850, 68.200, 1.150), (68.200, 1.150, 67.850, 1.220),
        (67.850, 1.220, 67.500, 0.950)]],
}
pool = {0: [], 1: [], 2: []}
for li in range(3):
    remkeys = set()
    for n, s in REM_SEGS.get(li, []):
        a, b = key_seg(s)
        remkeys.add((n, a)); remkeys.add((n, b))
    for it in items[li]:
        if it[0] == 'via' and it[1] == 'I2C_SDA' and \
           abs(it[2][0] - 69.9) < 0.01 and abs(it[2][1] - 0.82) < 0.01:
            continue
        if it[0] == 'seg':
            a, b = key_seg(it[2])
            if (it[1], a) in remkeys:
                continue
        pool[li].append(it)

def add_via(net, x, y, r=0.25):
    for li in range(3):
        pool[li].append(('via', net, (x, y, r), netclass(net)[1]))

def add_seg(li, net, a, b, w):
    pool[li].append(('seg', net, (a[0], a[1], b[0], b[1], w / 2),
                     netclass(net)[1]))

add_via('I2C_SDA', SX, SY)
add_via('HV_SHDN', *W); add_via('HV_SHDN', EX, EY)
add_via('HV_SHDN', *BW1); add_via('HV_SHDN', *BW2)
add_seg(1, 'HV_SHDN', (68.875, 0.625), W, 0.25)
add_seg(1, 'HV_SHDN', (EX, EY), (69.875, -0.375), 0.25)
add_seg(1, 'HV_SHDN', (67.375, 2.125), BW1, 0.25)
add_seg(1, 'HV_SHDN', BW2, (65.625, 3.875), 0.25)
add_seg(2, 'HV_SHDN', BW1, BW2, 0.25)
add_seg(2, 'HV_SHDN', W, (68.05, -4.70), 0.25)
add_seg(2, 'HV_SHDN', (68.05, -4.70), (69.00, -4.70), 0.25)
add_seg(2, 'HV_SHDN', (69.00, -4.70), (EX, EY), 0.25)
add_seg(2, 'I2C_SDA', (69.875, -1.5), (69.875, -9.125), 0.25)
add_seg(2, 'I2C_SDA', (69.875, -1.5), (SX, SY), 0.25)

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
    'CAP_CLK':  dict(start=(70.02, 1.83), target=(75.45, 25.385)),
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
        m = np.zeros((NY, NX), dtype=bool)
        for (_, iy, ix) in run:
            m[iy, ix] = True
        dil = ndimage.binary_dilation(m, structure=np.ones((17, 17)))
        sibling_block[l] |= dil
    for (vx, vy) in vias:
        vyi, vxi = cell(vx, vy)
        for l in range(3):
            sub = np.zeros((NY, NX), dtype=bool)
            sub[vyi, vxi] = True
            sibling_block[l] |= ndimage.binary_dilation(
                sub, structure=np.ones((29, 29)))
    fn = f"scratch/work/at/journey_{net}_{''.join(o[4] for o in ORDER)}.json"
    json.dump(out, open(fn, 'w'))
    print(f"   vias: {out['vias']}", flush=True)
    for r in out['runs']:
        print(f"   L{r['layer']}: {len(r['pts'])} pts "
              f"{r['pts'][0]} -> {r['pts'][-1]}", flush=True)
    print(f"   wrote {fn}", flush=True)
