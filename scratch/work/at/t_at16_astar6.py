"""t_at16: CAP pair A* in model v6.
Edits vs esc:
 - HV band jog v4+: rip 6 segs (68.625,0.875)..(70.125,-0.625);
   chain (68.625,0.875)->(68.75,0.5)->(69.0,0.25)->(69.25,0.0)->
   (69.5,-0.25)->(69.75,-0.5)->(70.125,-0.625).
 - I2C_SCL via (69.375,1.375) r0.30 -> (69.5,1.35) r0.25;
   In2 tail re-laid (68.875,1.625)->(69.5,1.35).
 - CAP_CLK escape via (70.02,1.83) -> (70.15,1.72); F feed re-laid
   (70.6,1.78)->(70.15,1.72).
 - SDA via S=(70.05,0.82); B vertical kept from -1.5; B diag to S.
 - GND F tree removed. +3V3D F web U5 removed; via (74.625,24.375)
   shrunk r0.40->0.25. XO In2 web removed.
Usage: t_at16_astar6.py [ORDER]"""
import wx
_app = wx.App(False)
import pcbnew, sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

ORDER = (sys.argv[1] if len(sys.argv) > 1 else 'CAP_CLK,CAP_DATA').split(',')
S = (70.05, 0.82)
SCL_VIA = (69.5, 1.35)
CLK_VIA = (70.15, 1.72)
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)

def key_seg(d):
    a = (round(d[0], 3), round(d[1], 3), round(d[2], 3), round(d[3], 3))
    b = (round(d[2], 3), round(d[3], 3), round(d[0], 3), round(d[1], 3))
    return a, b

BAND_RIP = [(68.625, 0.875, 68.875, 0.625),
            (68.875, 0.625, 69.125, 0.375), (69.125, 0.375, 69.375, 0.125),
            (69.375, 0.125, 69.625, -0.125),
            (69.625, -0.125, 69.875, -0.375),
            (69.875, -0.375, 70.125, -0.625)]
REM_SEGS = {
    1: [('HV_SHDN', s) for s in BAND_RIP] + [
        ('I2C_SCL', (68.875, 1.625, 69.375, 1.375))],
    0: [('CAP_CLK', (70.6, 1.78, 70.02, 1.83))] + [
        ('GND', s) for s in [
            (71.000, 0.270, 69.600, 0.250), (69.600, 0.250, 68.900, 0.850),
            (68.900, 0.850, 68.200, 1.150), (68.200, 1.150, 67.850, 1.220),
            (67.850, 1.220, 67.500, 0.950)]],
    2: [('I2C_SDA', s) for s in [
        (69.900, 0.820, 69.875, 0.625), (69.875, 0.625, 69.875, -9.125)]],
}
REM_VIAS = [(69.9, 0.82, 'I2C_SDA'), (69.375, 1.375, 'I2C_SCL'),
            (70.02, 1.83, 'CAP_CLK')]
pool = {0: [], 1: [], 2: []}
for li in range(3):
    remkeys = set()
    for n, s in REM_SEGS.get(li, []):
        a, b = key_seg(s)
        remkeys.add((n, a)); remkeys.add((n, b))
    for it in items[li]:
        if it[0] == 'via':
            skip = False
            for vx, vy, vn in REM_VIAS:
                if it[1] == vn and abs(it[2][0] - vx) < 0.01 and \
                   abs(it[2][1] - vy) < 0.01:
                    skip = True
            if skip:
                continue
            if it[1] == '+3V3D' and abs(it[2][0] - 74.625) < 0.01 and \
               abs(it[2][1] - 24.375) < 0.01:
                pool[li].append(('via', '+3V3D', (74.625, 24.375, 0.25),
                                 it[3]))
                continue
        if it[0] == 'seg':
            a, b = key_seg(it[2])
            if (it[1], a) in remkeys:
                continue
            cx = (it[2][0] + it[2][2]) / 2
            cy = (it[2][1] + it[2][3]) / 2
            if li == 0 and it[1] == '+3V3D' and 70 < cx < 76 and 20 < cy < 26:
                continue
            if li == 1 and it[1] == 'XO' and 66 < cx < 76 and 16 < cy < 23:
                continue
        pool[li].append(it)

NEW = []
def add_via(net, x, y, r=0.25):
    for li in range(3):
        pool[li].append(('via', net, (x, y, r), netclass(net)[1]))
    NEW.append((-1, ('via', net, (x, y, r), netclass(net)[1])))

def add_seg(li, net, a, b, w):
    pool[li].append(('seg', net, (a[0], a[1], b[0], b[1], w / 2),
                     netclass(net)[1]))
    NEW.append((li, ('seg', net, (a[0], a[1], b[0], b[1], w / 2),
                     netclass(net)[1])))

BANDV = [(68.625, 0.875), (68.75, 0.5), (69.0, 0.25), (69.25, 0.0),
         (69.5, -0.25), (69.75, -0.5), (70.125, -0.625)]
for i in range(len(BANDV) - 1):
    add_seg(1, 'HV_SHDN', BANDV[i], BANDV[i + 1], 0.25)
add_via('I2C_SCL', *SCL_VIA)
add_seg(1, 'I2C_SCL', (68.875, 1.625), SCL_VIA, 0.20)
add_via('CAP_CLK', *CLK_VIA)
add_seg(0, 'CAP_CLK', (70.6, 1.78), CLK_VIA, 0.20)
add_via('I2C_SDA', *S)
add_seg(2, 'I2C_SDA', (69.875, -1.5), (69.875, -9.125), 0.25)
add_seg(2, 'I2C_SDA', (69.875, -1.5), S, 0.25)

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
print(f'== pre-gate new copper: {m:+.3f}  {L.fmt_it(it)} vs {L.fmt_it(w)}',
      flush=True)

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
    'CAP_CLK':  dict(start=CLK_VIA, target=(75.45, 25.385)),
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
    fn = f"scratch/work/at/journey6_{net}_{''.join(o[4] for o in ORDER)}.json"
    json.dump(out, open(fn, 'w'))
    print(f"   vias: {out['vias']}", flush=True)
    for r in out['runs']:
        print(f"   L{r['layer']}: {len(r['pts'])} pts "
              f"{r['pts'][0]} -> {r['pts'][-1]}", flush=True)
    print(f"   wrote {fn}", flush=True)
