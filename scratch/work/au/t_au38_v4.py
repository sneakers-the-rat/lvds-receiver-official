"""t_au38: CAP pocket v4 + full final model.
Changes vs v3: CLK esc via (70.02,1.83)->(70.15,2.50) with re-laid
F stub and B entry; SDA via (69.2,2.2)->(69.05,2.05) with re-laid
stub/hop; SCL healed by B heal to the staircase (NOT ripped);
chord and long heal NOT used. DATA entry re-run. +3V3A heals at
hw0.10. PG/+3V3D/XO conflict rips + fragment heals.
Outputs: manifest_au38.json (all build items) + heal JSONs."""
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
# CLK esc via + its F stub (esc items)
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
nrip = sum(1 for l in range(3) for it in items_full[l]
           if any(p(l, it) for p in RIPS))
print(f'model rips: {nrip}', flush=True)
for it in U9PADS:
    d = it[2]
    pool[0].append(('pad', it[1], (d[0] - 1.0, d[1], d[2], d[3], d[4]),
                    it[3]))

NEW = {0: [], 1: [], 2: []}


def seg_(store, l, net, a, b, hw=0.10, clr=0.2):
    store[l].append(('seg', net, (a[0], a[1], b[0], b[1], hw), clr))


def via_(store, net, x, y, r=0.25, clr=0.2):
    for l in range(3):
        store[l].append(('via', net, (x, y, r), clr))


# pocket v4 fixed items
via_(NEW, 'I2C_SCL', 69.35, 1.40)
via_(NEW, 'I2C_SDA', 69.05, 2.05)
seg_(NEW, 0, 'I2C_SDA', (68.45, 2.1), (69.05, 2.05))
seg_(NEW, 1, 'I2C_SDA', (69.05, 2.05), (69.9, 1.85), hw=0.125)
seg_(NEW, 1, 'I2C_SDA', (69.9, 1.85), (70.6, 1.82), hw=0.125)
seg_(NEW, 1, 'I2C_SDA', (70.6, 1.82), (71.125, 1.875), hw=0.125)
STAIR = [(69.9, 0.82), (70.125, 0.875), (70.375, 1.125), (70.625, 1.375),
         (70.875, 1.625), (71.125, 1.875)]
for a, b in zip(STAIR, STAIR[1:]):
    seg_(NEW, 1, 'I2C_SDA', a, b, hw=0.125)
seg_(NEW, 0, 'GND', (67.625, 3.875), (67.45, 3.55))
BOW = [(71.125, 1.875), (71.6, 2.4), (71.7, 3.55), (71.125, 4.125)]
for a, b in zip(BOW, BOW[1:]):
    seg_(NEW, 1, 'I2C_SDA', a, b, hw=0.125)
TMP = [(66.275, 3.4), (65.95, 3.35), (65.7, 3.15), (65.7, 2.2),
       (65.7, -2.6), (66.125, -3.125)]
for a, b in zip(TMP, TMP[1:]):
    seg_(NEW, 0, 'TMP_ALERT', a, b, hw=0.125 if b[1] < 0 else 0.10)
# CLK v4 head: stub + via + B entry (ride rejoins at (69.55,2.7))
via_(NEW, 'CAP_CLK', 70.15, 2.50)
seg_(NEW, 0, 'CAP_CLK', (71.338, 1.75), (70.15, 2.50))
seg_(NEW, 2, 'CAP_CLK', (70.15, 2.50), (69.85, 2.60))
seg_(NEW, 2, 'CAP_CLK', (69.85, 2.60), (69.55, 2.70))
# SCL B heal
seg_(NEW, 2, 'I2C_SCL', (69.35, 1.40), (70.0, 1.90))
seg_(NEW, 2, 'I2C_SCL', (70.0, 1.90), (70.55, 2.20))
seg_(NEW, 2, 'I2C_SCL', (70.55, 2.20), (70.875, 2.625))
for l in range(3):
    pool[l] += NEW[l]

# CLK journey with head replaced: drop original head items (vias
# (70.02,1.83) and B run pts before (69.55,2.7) and F run)
J9 = json.load(open('scratch/work/au/journey_au9_CLK.json'))


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


# CLK9 runs: [F stub][B ride][In2 ride][F][In2][F arrival...]; rebuild
# B ride starting at (69.55,2.7): find B run and truncate its head
runs9 = []
for run in J9['runs']:
    pts = [tuple(p) for p in run['pts']]
    if run['layer'] == 0 and abs(pts[0][1] - 1.83) < 0.3 and pts[0][0] > 69:
        continue  # old F stub
    if run['layer'] == 2:
        # truncate to first point at/after (69.55,2.7) vicinity
        idx = min(range(len(pts)),
                  key=lambda i: math.hypot(pts[i][0] - 69.55,
                                           pts[i][1] - 2.7))
        runs9.append(dict(layer=2, pts=[list(p) for p in pts[idx:]]))
    else:
        runs9.append(run)
clkJ = dict(vias=[v for v in J9['vias']
                  if not (abs(v[0] - 70.02) < 0.1 and abs(v[1] - 1.83) < 0.1)],
            runs=runs9)
clk_items = journey_items_dense(clkJ, 'CAP_CLK')
for l in range(3):
    pool[l] += clk_items[l]
json.dump(clkJ, open('scratch/work/au/journey_au38_CLK.json', 'w'))

# gate the fixed NEW items vs pool (excluding own net)
def gate_new():
    bad = 0
    for l in range(3):
        for it in NEW[l]:
            others = [o for o in pool[l] if o[1] != it[1]
                      and o is not it]
            if it[0] == 'seg':
                d = it[2]
                m, w = L.seg_margin(l, (d[0], d[1]), (d[2], d[3]),
                                    it[1], d[4], others)
            else:
                d = it[2]
                m, w = L.pt_margin(l, d[0], d[1], it[1], d[2], others)
            if m < 0:
                bad += 1
                print(f'  GATE FAIL L{l} {L.fmt_it(it)} {m:+.3f} vs '
                      f'{L.fmt_it(w)}', flush=True)
    print(f'fixed-item gate failures: {bad}', flush=True)


gate_new()

# ---------- A* machinery ----------
def make_astar(box, step):
    FX0, FX1, FY0, FY1, FST = box[0], box[1], box[2], box[3], step
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

    def astar(net, start, goal, hw=0.10):
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
                vias.append((float(fxs[cur[-1][2]]),
                             float(fys[cur[-1][1]])))
                cur = [p]
        runs.append(cur)
        out = dict(vias=[[round(a, 3), round(b, 3)] for a, b in vias],
                   runs=[])
        for run in runs:
            pp = [(float(fxs[q[2]]), float(fys[q[1]])) for q in run]
            out['runs'].append(dict(layer=int(run[0][0]),
                                    pts=[[round(a, 3), round(b, 3)]
                                         for a, b in pp]))
        return out
    return astar


def add_j(J, net, hw=0.10):
    items = journey_items_dense(J, net, hw)
    for l in range(3):
        pool[l] += items[l]


def show(name, J):
    if J is None:
        print(f'{name}: NONE', flush=True)
        return False
    print(f'{name}: FOUND vias={J["vias"]}', flush=True)
    for r in J['runs']:
        print(f'   L{r["layer"]}: {r["pts"][0]} -> {r["pts"][-1]} '
              f'({len(r["pts"])} pts)', flush=True)
    return True


heals = {}
# DATA entry re-run in v4 fences
astarD = make_astar((62.0, 73.0, -1.0, 9.0), 0.025)
J30 = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
pts0 = J30['runs'][0]['pts']
REJOIN = tuple(pts0[213])
J = astarD('CAP_DATA', ((0, 1, 2), 69.9, 3.18), (1, REJOIN[0], REJOIN[1]))
if show('DATA entry v4', J):
    add_j(J, 'CAP_DATA')
    heals['data_entry'] = J
    tail = dict(net='CAP_DATA', vias=J30['vias'],
                runs=[dict(layer=1, pts=pts0[213:])] + J30['runs'][1:])
    for l in range(3):
        pool[l] += journey_items_dense(tail, 'CAP_DATA')[l]
    heals['data_tail'] = tail

# SCL F fanout re-run
astarF = make_astar((62.0, 73.0, -1.0, 9.0), 0.025)
J = astarF('I2C_SCL', ((0,), 69.35, 1.40), (0, 66.275, 2.10))
if show('SCL F fanout v4', J):
    add_j(J, 'I2C_SCL')
    heals['scl_ffan'] = J

# +3V3A heals at hw 0.10
astarA = make_astar((66.0, 72.5, -0.5, 6.0), 0.025)
J = astarA('+3V3A', ((0,), 68.225, 2.75), (0, 69.125, 4.375))
if show('+3V3A heal1 v4', J):
    add_j(J, '+3V3A')
    heals['p3a_1'] = J
J = astarA('+3V3A', ((0,), 71.375, 0.875), (0, 69.125, 4.375))
if show('+3V3A heal2 v4', J):
    add_j(J, '+3V3A')
    heals['p3a_2'] = J

json.dump(heals, open('scratch/work/au/heals_au38.json', 'w'))
print('phase1 done', flush=True)
