"""t_au18: pocket A* chain in the rebuilt-pocket model.
Base model: t_au17 pocket (rips + U9 west + SCL via + SDA via/hop/
staircase + GND chain + TMP re-lay) + CLK9 dense + settled-model
ablations (PG corridor out, P3F out, XO box out) for outside-pocket
fences. DATA30 remainder items (from rejoin (65.35,4.65)) fenced.
Chain (each A* at 0.025 in pocket box, items accumulate):
 1. DATA entry: (any layer, 69.9,3.18) -> (In2, 65.35,4.65)
 2. SCL chord: (any, 69.35,1.40) -> (In2, 67.875,5.125)
 3. SCL B heal: (B, 69.35,1.40) -> (B, 70.875,2.625)
 4. SCL F fanout: (F, 69.35,1.40) -> (F, 66.275,2.10)
If step 2 fails, retry order B: chord first (slot wall sum>=70.0
fenced for the chord's SW side is NOT used; plain), then DATA."""
import sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
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


RIPS = []
RIPS.append(lambda l, it: it[0] == 'via' and it[1] == 'I2C_SCL'
            and near(it, 69.375, 1.375))
RIPS.append(lambda l, it: l == 0 and it[1] == 'I2C_SCL' and it[0] == 'seg'
            and 66.8 < C(it)[0] < 69.6 and 1.0 < C(it)[1] < 2.2)
RIPS.append(lambda l, it: l == 1 and it[1] == 'I2C_SCL' and it[0] == 'seg'
            and ((abs(it[2][0] - 67.875) < 0.01 and abs(it[2][1] - 5.125) < 0.01)
                 or (abs(it[2][0] - 69.375) < 0.01
                     and abs(it[2][1] - 1.375) < 0.01)))
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
U9PADS = []
for it in items_full[0]:
    if it[0] == 'pad' and 66.5 < it[2][0] < 70.0 and 1.5 < it[2][1] < 4.0 \
            and it[1] in ('I2C_SCL', 'GND', 'TMP_ALERT', '+3V3A', 'I2C_SDA'):
        U9PADS.append(it)
RIPS.append(lambda l, it: it in U9PADS)
PG_PRED = lambda l, it: l == 2 and it[1] == 'PG_3V3' \
    and 60 < C(it)[0] < 70 and 0 < C(it)[1] < 16
P3F_PRED = lambda l, it: l == 0 and it[1] == '+3V3D' \
    and it[0] in ('seg', 'via') \
    and 68 < C(it)[0] < 77 and 19 < C(it)[1] < 27
XO_PRED = lambda l, it: l == 1 and it[1] == 'XO' \
    and 66 < C(it)[0] < 76 and 16 < C(it)[1] < 23
for P in (PG_PRED, P3F_PRED, XO_PRED):
    RIPS.append(P)

pool = {l: [it for it in items_full[l]
            if not any(p(l, it) for p in RIPS)] for l in range(3)}
for it in U9PADS:
    d = it[2]
    pool[0].append(('pad', it[1], (d[0] - 1.0, d[1], d[2], d[3], d[4]),
                    it[3]))


def journey_items_dense(J, net):
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
            out[l].append(('seg', net, (a[0], a[1], b[0], b[1], 0.10), 0.2))
    for (vx, vy) in J['vias']:
        for l in range(3):
            out[l].append(('via', net, (vx, vy, 0.25), 0.2))
    return out


clk_items = journey_items_dense(
    json.load(open('scratch/work/au/journey_au9_CLK.json')), 'CAP_CLK')
J30 = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
pts0 = [tuple(p) for p in J30['runs'][0]['pts']]
cand = min(range(len(pts0)),
           key=lambda i: math.hypot(pts0[i][0] - 65.3, pts0[i][1] - 4.6))
REJOIN = pts0[cand]
rem_J = dict(net='CAP_DATA', vias=J30['vias'],
             runs=[dict(layer=1, pts=[list(p) for p in pts0[cand:]])]
             + J30['runs'][1:])
data_rem = journey_items_dense(rem_J, 'CAP_DATA')

NEW = {0: [], 1: [], 2: []}


def seg_(store, l, net, a, b, hw=0.10, clr=0.2):
    store[l].append(('seg', net, (a[0], a[1], b[0], b[1], hw), clr))


def via_(store, net, x, y, r=0.25, clr=0.2):
    for l in range(3):
        store[l].append(('via', net, (x, y, r), clr))


via_(NEW, 'I2C_SCL', 69.35, 1.40)
via_(NEW, 'I2C_SDA', 69.2, 2.2)
seg_(NEW, 0, 'I2C_SDA', (68.45, 2.1), (69.2, 2.2))
seg_(NEW, 1, 'I2C_SDA', (69.2, 2.2), (70.35, 2.6), hw=0.125)
seg_(NEW, 1, 'I2C_SDA', (70.35, 2.6), (71.125, 1.875), hw=0.125)
STAIR = [(69.9, 0.82), (70.125, 0.875), (70.375, 1.125), (70.625, 1.375),
         (70.875, 1.625), (71.125, 1.875)]
for a, b in zip(STAIR, STAIR[1:]):
    seg_(NEW, 1, 'I2C_SDA', a, b, hw=0.125)
seg_(NEW, 0, 'GND', (67.625, 3.875), (67.45, 3.55))
TMP = [(66.275, 3.4), (65.95, 3.35), (65.7, 3.15), (65.7, 2.2),
       (65.7, -2.6), (66.125, -3.125)]
for a, b in zip(TMP, TMP[1:]):
    seg_(NEW, 0, 'TMP_ALERT', a, b, hw=0.125 if b[1] < 0 else 0.10)
for l in range(3):
    pool[l] += NEW[l] + clk_items[l] + data_rem[l]

# ---- fine A* machinery (box pocket)
FX0, FX1, FY0, FY1, FST = 62.0, 72.0, -1.0, 9.0, 0.025
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


def build_G(net, extra_block=None):
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
        if extra_block is not None:
            f = np.where(extra_block(l), -9.9, f)
        G[l] = f
    return G


def fcell(x, y):
    return (int(round((y - FY0) / FST)), int(round((x - FX0) / FST)))


def astar(net, start, goal, hw=0.10):
    """start=(layers_allowed, x, y), goal=(layer, x, y). Track legal
    field >= hw; via needs min field >= 0.25 (d0.5 vias)."""
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
        _, g, p = heapq.heappop(openh)
        if g > gs.get(p, 1e18) + 1e-9:
            continue
        l, iy, ix = p
        if l == goal[0] and (iy, ix) == tc:
            goalp = p
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
                if not (0 <= jy < FNY and 0 <= jx < FNX):
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
    if goalp is None:
        return None
    path = []
    p = goalp
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
    out = dict(vias=[[round(a, 3), round(b, 3)] for a, b in vias], runs=[])
    for run in runs:
        pp = [(float(fxs[q[2]]), float(fys[q[1]])) for q in run]
        out['runs'].append(dict(layer=int(run[0][0]),
                                pts=[[round(a, 3), round(b, 3)]
                                     for a, b in pp]))
    return out


def add_journey(J, net, hw=0.10):
    items = journey_items_dense(J, net)
    # journey_items_dense uses hw 0.10 segs; ok for CAP/SCL (w0.2)
    for l in range(3):
        pool[l] += items[l]
    return items


def show(name, J):
    if J is None:
        print(f'{name}: NONE', flush=True)
        return False
    print(f'{name}: FOUND vias={J["vias"]}', flush=True)
    for r in J['runs']:
        print(f'   L{r["layer"]}: {r["pts"][0]} -> {r["pts"][-1]} '
              f'({len(r["pts"])} pts)', flush=True)
    return True


order = sys.argv[1] if len(sys.argv) > 1 else 'A'
res = {}
if order == 'A':
    J = astar('CAP_DATA', ((0, 1, 2), 69.9, 3.18), (1, REJOIN[0], REJOIN[1]))
    res['data_entry'] = J
    if show('DATA entry', J):
        add_journey(J, 'CAP_DATA')
        json.dump(J, open('scratch/work/au/entry_au18_DATA.json', 'w'))
    J = astar('I2C_SCL', ((0, 1, 2), 69.35, 1.40), (1, 67.875, 5.125))
    res['scl_chord'] = J
    if show('SCL chord', J):
        add_journey(J, 'I2C_SCL')
        json.dump(J, open('scratch/work/au/chord_au18_SCL.json', 'w'))
else:
    J = astar('I2C_SCL', ((0, 1, 2), 69.35, 1.40), (1, 67.875, 5.125))
    res['scl_chord'] = J
    if show('SCL chord', J):
        add_journey(J, 'I2C_SCL')
        json.dump(J, open('scratch/work/au/chord_au18_SCL.json', 'w'))
    J = astar('CAP_DATA', ((0, 1, 2), 69.9, 3.18), (1, REJOIN[0], REJOIN[1]))
    res['data_entry'] = J
    if show('DATA entry', J):
        add_journey(J, 'CAP_DATA')
        json.dump(J, open('scratch/work/au/entry_au18_DATA.json', 'w'))

J = astar('I2C_SCL', ((2,), 69.35, 1.40), (2, 70.875, 2.625))
if show('SCL B heal', J):
    add_journey(J, 'I2C_SCL')
    json.dump(J, open('scratch/work/au/bheal_au18_SCL.json', 'w'))
J = astar('I2C_SCL', ((0,), 69.35, 1.40), (0, 66.275, 2.10))
if show('SCL F fanout', J):
    add_journey(J, 'I2C_SCL')
    json.dump(J, open('scratch/work/au/ffan_au18_SCL.json', 'w'))
print('done', flush=True)
