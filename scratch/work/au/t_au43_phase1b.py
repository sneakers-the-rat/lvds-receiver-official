"""t_au43: v5 phase-1 completion. Model = esc - rips + FIXED +
CLK via (70.2,1.8) + stub + joint_au40 journeys (bheal/hop/exit).
Then: DATA entry (In2, from (69.9,3.18) to (63.85,6.3)) + DATA30
tail; +3V3A heal1; +3V3A heal2 (widest diag if NONE)."""
import wx
_app = wx.App(False)
import sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_au1_lib as U
import t_ai_lib as L
import pcbnew
from router import netclass

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items_full = L.load_items(board)
C = U.item_centre


def near(it, x, y, tol=0.01):
    c = C(it)
    return abs(c[0] - x) < tol and abs(c[1] - y) < tol


DIAG_ENDS = {(67.875, 5.125), (69.375, 1.375), (68.875, 1.625)}
RIPS = []
RIPS.append(lambda l, it: it[0] == 'via' and it[1] == 'I2C_SCL'
            and near(it, 69.375, 1.375))
RIPS.append(lambda l, it: l == 0 and it[1] == 'I2C_SCL' and it[0] == 'seg'
            and 66.8 < C(it)[0] < 69.6 and 1.0 < C(it)[1] < 2.2)
RIPS.append(lambda l, it: l == 1 and it[1] == 'I2C_SCL' and it[0] == 'seg'
            and ((round(it[2][0], 3), round(it[2][1], 3)) in DIAG_ENDS
                 or (round(it[2][2], 3), round(it[2][3], 3)) in DIAG_ENDS))
RIPS.append(lambda l, it: it[0] == 'via' and it[1] == 'I2C_SDA'
            and near(it, 69.320, 2.140))
RIPS.append(lambda l, it: l == 0 and it[1] == 'GND' and it[0] == 'seg'
            and ((abs(it[2][0] - 68.25) < 0.01 and abs(it[2][1] - 3.5) < 0.01)
                 or (abs(it[2][2] - 68.25) < 0.01
                     and abs(it[2][3] - 3.5) < 0.01)))
RIPS.append(lambda l, it: l == 0 and it[1] == 'TMP_ALERT' and it[0] == 'seg'
            and C(it)[0] < 67.3 and C(it)[1] > -3.2)
RIPS.append(lambda l, it: l == 0 and it[1] == '+3V3A' and it[0] == 'seg'
            and abs(it[2][0] - 69.225) < 0.01 and abs(it[2][1] - 2.75) < 0.01
            and abs(it[2][2] - 69.475) < 0.01 and abs(it[2][3] - 2.75) < 0.01)
RIPS.append(lambda l, it: it[0] == 'via' and it[1] == 'CAP_CLK'
            and near(it, 70.020, 1.830))
RIPS.append(lambda l, it: l == 0 and it[1] == 'CAP_CLK' and it[0] == 'seg'
            and C(it)[0] > 69.8 and C(it)[1] < 2.2)
U9PADS = []
for it in items_full[0]:
    if it[0] == 'pad' and 66.5 < it[2][0] < 70.0 and 1.5 < it[2][1] < 4.0 \
            and it[1] in ('I2C_SCL', 'GND', 'TMP_ALERT', '+3V3A', 'I2C_SDA'):
        U9PADS.append(it)
RIPS.append(lambda l, it: it in U9PADS)
FRAG_PRED = lambda l, it: l == 1 and it[1] == 'I2C_SDA' and it[0] == 'seg' \
    and it[2][0] >= 71.1 and it[2][2] >= 71.1 \
    and 1.8 < it[2][1] < 4.2 and 1.8 < it[2][3] < 4.2
RIPS.append(FRAG_PRED)
pool = {l: [it for it in items_full[l]
            if not any(p(l, it) for p in RIPS)] for l in range(3)}
for it in U9PADS:
    d = it[2]
    pool[0].append(('pad', it[1], (d[0] - 1.0, d[1], d[2], d[3], d[4]),
                    it[3]))


def seg_(store, l, net, a, b, hw=0.10, clr=0.2):
    store[l].append(('seg', net, (a[0], a[1], b[0], b[1], hw), clr))


def via_(store, net, x, y, r=0.25, clr=0.2):
    for l in range(3):
        store[l].append(('via', net, (x, y, r), clr))


FIXED = {0: [], 1: [], 2: []}
via_(FIXED, 'I2C_SCL', 69.35, 1.40)
via_(FIXED, 'I2C_SDA', 69.05, 2.05)
seg_(FIXED, 0, 'I2C_SDA', (68.45, 2.1), (69.05, 2.05))
STAIR = [(69.9, 0.82), (70.125, 0.875), (70.375, 1.125), (70.625, 1.375),
         (70.875, 1.625), (71.125, 1.875)]
for a, b in zip(STAIR, STAIR[1:]):
    seg_(FIXED, 1, 'I2C_SDA', a, b, hw=0.125)
seg_(FIXED, 0, 'GND', (67.625, 3.875), (67.45, 3.55))
BOW = [(71.125, 1.875), (71.6, 2.4), (71.7, 3.55), (71.125, 4.125)]
for a, b in zip(BOW, BOW[1:]):
    seg_(FIXED, 1, 'I2C_SDA', a, b, hw=0.125)
TMP = [(66.275, 3.4), (65.95, 3.35), (65.7, 3.15), (65.7, 2.2),
       (65.7, -2.6), (66.125, -3.125)]
for a, b in zip(TMP, TMP[1:]):
    seg_(FIXED, 0, 'TMP_ALERT', a, b, hw=0.125 if b[1] < 0 else 0.10)
for l in range(3):
    pool[l] += FIXED[l]
def journey_items_dense(J, net, hw=0.10):
    out = {0: [], 1: [], 2: []}
    for run in J['runs']:
        l = run['layer']
        pts = [tuple(p) for p in run['pts']]
        keep = [pts[0]]
        for a, b, c in zip(pts, pts[1:], pts[2:]):
            v1 = (round(b[0] - a[0], 6), round(b[1] - a[1], 6))
            v2 = (round(c[0] - b[0], 6), round(c[1] - b[1], 6))
            if v1 != v2:
                keep.append(b)
        keep.append(pts[-1])
        for a, b in zip(keep, keep[1:]):
            out[l].append(('seg', net, (a[0], a[1], b[0], b[1], hw), 0.2))
    for (vx, vy) in J['vias']:
        for l in range(3):
            out[l].append(('via', net, (vx, vy, 0.25), 0.2))
    return out


# CLK v5
via_(pool, 'CAP_CLK', 70.2, 1.8)
seg_(pool, 0, 'CAP_CLK', (71.338, 1.75), (70.62, 1.79))
seg_(pool, 0, 'CAP_CLK', (70.62, 1.79), (70.2, 1.8))
J40 = json.load(open('scratch/work/au/joint_au40.json'))
for nm in ('bheal', 'hop', 'exit'):
    J = J40['jobs'][nm]
    net = {'bheal': 'I2C_SCL', 'hop': 'I2C_SDA', 'exit': 'CAP_CLK'}[nm]
    hw = 0.125 if nm == 'hop' else 0.10
    for l, its in journey_items_dense(J, net, hw=hw).items():
        pool[l] += its

print('v5 model built', flush=True)

def add_j(J, net, hw=0.10):
    for l, its in journey_items_dense(J, net, hw=hw).items():
        pool[l] += its


def entry_astar(net, layer, sx, sy, gx_, gy_, box, step=0.025, hw=0.10):
    X0, X1, Y0, Y1 = box
    xs = np.arange(X0, X1 + 1e-9, step)
    ys = np.arange(Y0, Y1 + 1e-9, step)
    GXm, GYm = np.meshgrid(xs, ys)
    NYm, NXm = GXm.shape
    myclr = netclass(net)[1]
    f = np.full(GXm.shape, 9.9)
    for it in pool[layer]:
        if it[1] == net:
            continue
        kind, d = it[0], it[2]
        bx0 = (d[0] - 1.6) if kind != 'seg' else min(d[0], d[2]) - 1.6
        bx1 = (d[0] + 1.6) if kind != 'seg' else max(d[0], d[2]) + 1.6
        by0 = (d[1] - 1.6) if kind != 'seg' else min(d[1], d[3]) - 1.6
        by1 = (d[1] + 1.6) if kind != 'seg' else max(d[1], d[3]) + 1.6
        req = max(myclr, it[3])
        if bx1 < X0 or bx0 > X1 or by1 < Y0 or by0 > Y1:
            continue
        if kind == 'pad':
            cx, cy, phw, phh, rot = d
            dx, dy = GXm - cx, GYm - cy
            c, s = math.cos(-rot), math.sin(-rot)
            lx, ly = dx * c - dy * s, dx * s + dy * c
            dd = np.hypot(np.maximum(np.abs(lx) - phw, 0.0),
                          np.maximum(np.abs(ly) - phh, 0.0))
        elif kind == 'seg':
            x1, y1, x2, y2, shw = d
            px, py = GXm - x1, GYm - y1
            dx, dy = x2 - x1, y2 - y1
            L2 = dx * dx + dy * dy
            t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
            dd = np.hypot(px - t * dx, py - t * dy) - shw
        else:
            dd = np.hypot(GXm - d[0], GYm - d[1]) - d[2]
        f = np.minimum(f, dd - req)
    ok = f >= hw
    sc = (int(round((sy - Y0) / step)), int(round((sx - X0) / step)))
    tc = (int(round((gy_ - Y0) / step)), int(round((gx_ - X0) / step)))

    def h(p):
        return math.hypot(p[0] - tc[0], p[1] - tc[1])
    openh, came, gs = [], {}, {sc: 0.0}
    came[sc] = None
    heapq.heappush(openh, (h(sc), 0.0, sc))
    goalp = None
    while openh:
        _, gg, p = heapq.heappop(openh)
        if gg > gs.get(p, 1e18) + 1e-9:
            continue
        if p == tc:
            goalp = p
            break
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                q = (p[0] + dy, p[1] + dx)
                if not (0 <= q[0] < NYm and 0 <= q[1] < NXm):
                    continue
                if not ok[q]:
                    continue
                stp = 1.414 if dx and dy else 1.0
                pen = max(0.0, 0.55 - f[q]) * 6.0
                ng = gg + stp + pen
                if ng < gs.get(q, 1e18) - 1e-9:
                    gs[q] = ng
                    came[q] = p
                    heapq.heappush(openh, (ng + h(q), ng, q))
    if goalp is None:
        return None
    path, p = [], goalp
    while p is not None:
        path.append(p)
        p = came[p]
    path.reverse()
    pts = [[round(float(xs[q[1]]), 3), round(float(ys[q[0]]), 3)]
           for q in path]
    return dict(vias=[], runs=[dict(layer=layer, pts=pts)])


out = {}
J = entry_astar('CAP_DATA', 1, 69.9, 3.175, 63.85, 6.3,
                (60.0, 72.0, -1.0, 10.0))
print('DATA entry v5:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['data_entry'] = J
    add_j(J, 'CAP_DATA')
    J30 = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
    pts0 = J30['runs'][0]['pts']
    TAIL = dict(vias=J30['vias'],
                runs=[dict(layer=1, pts=pts0[213:])] + J30['runs'][1:])
    out['data_tail'] = TAIL
    for l, its in journey_items_dense(TAIL, 'CAP_DATA').items():
        pool[l] += its

FBOX = (66.0, 72.5, -0.5, 6.0)
FST = 0.025
FX0, FX1, FY0, FY1 = FBOX
fxs = np.arange(FX0, FX1 + 1e-9, FST)
fys = np.arange(FY0, FY1 + 1e-9, FST)
FGX, FGY = np.meshgrid(fxs, fys)
FNY, FNX = FGX.shape


def dist_field(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = FGX - cx, FGY - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = FGX - x1, FGY - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    cx, cy, r = d
    return np.hypot(FGX - cx, FGY - cy) - r


def bbox(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        r = math.hypot(d[2], d[3])
        return d[0] - r, d[0] + r, d[1] - r, d[1] + r
    if kind == 'seg':
        return (min(d[0], d[2]) - d[4], max(d[0], d[2]) + d[4],
                min(d[1], d[3]) - d[4], max(d[1], d[3]) + d[4])
    return d[0] - d[2], d[0] + d[2], d[1] - d[2], d[1] + d[2]


def build_G(net):
    myclr = netclass(net)[1]
    G = {}
    for l in range(3):
        f = np.full(FGX.shape, 9.9)
        for it in pool[l]:
            if it[1] == net:
                continue
            bx0, bx1, by0, by1 = bbox(it)
            req = max(myclr, it[3])
            if bx1 < FX0 - req - 0.3 or bx0 > FX1 + req + 0.3 or \
               by1 < FY0 - req - 0.3 or by0 > FY1 + req + 0.3:
                continue
            f = np.minimum(f, dist_field(it) - req)
        G[l] = f
    return G


def fcell(x, y):
    return (int(round((y - FY0) / FST)), int(round((x - FX0) / FST)))


def fastest(net, start, goal, hw=0.10):
    G = build_G(net)
    track = {l: G[l] >= hw for l in range(3)}
    viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
    sc = fcell(start[1], start[2])
    tc = fcell(goal[1], goal[2])

    def h(p):
        return math.hypot(p[1] - tc[0], p[2] - tc[1])
    openh, came, gs = [], {}, {}
    for l in start[0]:
        s0 = (l, sc[0], sc[1])
        if track[l][sc[0], sc[1]]:
            gs[s0] = 0.0
            came[s0] = None
            heapq.heappush(openh, (h(s0), 0.0, s0))
    goalp = None
    while openh:
        _, gg, p = heapq.heappop(openh)
        if gg > gs.get(p, 1e18) + 1e-9:
            continue
        l, iy, ix = p
        if l == goal[0] and (iy, ix) == tc:
            goalp = p
            break
        for l2 in range(3):
            if l2 != l and viafit[iy, ix] and track[l2][iy, ix]:
                q = (l2, iy, ix)
                ng = gg + 6.0
                if ng < gs.get(q, 1e18) - 1e-9:
                    gs[q] = ng
                    came[q] = p
                    heapq.heappush(openh, (ng + h(q), ng, q))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                jy, jx = iy + dy, ix + dx
                if not (0 <= jy < FNY and 0 <= jx < FNX):
                    continue
                if not track[l][jy, jx]:
                    continue
                stp = 1.414 if dx and dy else 1.0
                pen = max(0.0, 0.55 - G[l][jy, jx]) * 6.0
                ng = gg + stp + pen
                q = (l, jy, jx)
                if ng < gs.get(q, 1e18) - 1e-9:
                    gs[q] = ng
                    came[q] = p
                    heapq.heappush(openh, (ng + h(q), ng, q))
    if goalp is None:
        return None
    path, p = [], goalp
    while p is not None:
        path.append(p)
        p = came[p]
    path.reverse()
    runs, vias, cur = [], [], [path[0]]
    for p in path[1:]:
        if p[0] == cur[-1][0]:
            cur.append(p)
        else:
            runs.append(cur)
            vias.append((float(fxs[cur[-1][2]]), float(fys[cur[-1][1]])))
            cur = [p]
    runs.append(cur)
    o = dict(vias=[[round(a, 3), round(b, 3)] for a, b in vias], runs=[])
    for run in runs:
        pp = [(float(fxs[q[2]]), float(fys[q[1]])) for q in run]
        o['runs'].append(dict(layer=int(run[0][0]),
                              pts=[[round(a, 3), round(b, 3)]
                                   for a, b in pp]))
    return o


J = fastest('+3V3A', ((0,), 68.225, 2.75), (0, 69.125, 4.375), hw=0.10)
print('+3V3A heal1 v5:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['v3a_heal1'] = J
    add_j(J, '+3V3A', 0.10)
J = fastest('+3V3A', ((0,), 71.375, 0.875), (0, 69.125, 4.375), hw=0.10)
print('+3V3A heal2 v5:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['v3a_heal2'] = J
    add_j(J, '+3V3A', 0.10)
json.dump(out, open('scratch/work/au/heals_au43.json', 'w'))
print('phase1b done', flush=True)
