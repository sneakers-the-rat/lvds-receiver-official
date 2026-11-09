"""t_au71: phase 2b. Full final model (CLK9 correctly truncated),
conflict rips for PG_3V3/+3V3D/XO, fragment detours, fanout +
heal2 retries, FULL exact gate, connectivity check. Saves
build_au71.json (rips + all journeys + fixed items)."""
import wx
_app = wx.App(False)
import sys, json, math, heapq
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
    pool[0].append(('pad', it[1], (d[0] - 1.25, d[1], d[2], d[3], d[4]),
                    it[3]))


def seg_(store, l, net, a, b, hw=0.10, clr=0.2):
    store[l].append(('seg', net, (a[0], a[1], b[0], b[1], hw), clr))


def via_(store, net, x, y, r=0.25, clr=0.2):
    for l in range(3):
        store[l].append(('via', net, (x, y, r), clr))


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


FIXED = {0: [], 1: [], 2: []}
via_(FIXED, 'I2C_SCL', 69.35, 1.40)
via_(FIXED, 'I2C_SDA', 69.05, 2.05)
seg_(FIXED, 0, 'I2C_SDA', (67.975, 2.1), (69.05, 2.05))
STAIR = [(69.9, 0.82), (70.125, 0.875), (70.375, 1.125), (70.625, 1.375),
         (70.875, 1.625), (71.125, 1.875)]
for a, b in zip(STAIR, STAIR[1:]):
    seg_(FIXED, 1, 'I2C_SDA', a, b, hw=0.125)
seg_(FIXED, 0, 'GND', (67.625, 3.875), (67.45, 3.55))
BOW = [(71.125, 1.875), (71.6, 2.4), (71.7, 3.55), (71.125, 4.125)]
for a, b in zip(BOW, BOW[1:]):
    seg_(FIXED, 1, 'I2C_SDA', a, b, hw=0.125)
TMP = [(66.025, 3.4), (65.95, 3.35), (65.7, 3.15), (65.7, 2.2),
       (65.7, -2.6), (66.125, -3.125)]
for a, b in zip(TMP, TMP[1:]):
    seg_(FIXED, 0, 'TMP_ALERT', a, b, hw=0.125 if b[1] < 0 else 0.10)
for l in range(3):
    pool[l] += FIXED[l]
via_(pool, 'CAP_CLK', 70.2, 1.8)
seg_(pool, 0, 'CAP_CLK', (71.338, 1.75), (70.62, 1.79))
seg_(pool, 0, 'CAP_CLK', (70.62, 1.79), (70.2, 1.8))

NEW = {0: [], 1: [], 2: []}
JOURNEYS = {}


def add_new(name, J, net, hw=0.10):
    JOURNEYS[name] = J
    for l, its in journey_items_dense(J, net, hw=hw).items():
        NEW[l] += its
        pool[l] += its


J40 = json.load(open('scratch/work/au/joint_au40.json'))
add_new('bheal', J40['jobs']['bheal'], 'I2C_SCL', 0.10)
add_new('hop', J40['jobs']['hop'], 'I2C_SDA', 0.125)
J67 = json.load(open('scratch/work/au/heals_au67.json'))
add_new('v3a_heal1', J67['v3a_heal1'], '+3V3A', 0.10)
add_new('clk_exit_frun', J67['clk_exit_frun'], 'CAP_CLK', 0.10)
for l in range(3):
    it = ('via', 'CAP_CLK', (69.075, 2.8, 0.25), 0.2)
    NEW[l].append(it)
    pool[l].append(it)
bj = ('seg', 'CAP_CLK', (69.075, 2.8, 69.55, 2.7, 0.10), 0.2)
NEW[2].append(bj)
pool[2].append(bj)
add_new('data_entry', J67['data_entry'], 'CAP_DATA', 0.10)
add_new('data_tail', J67['data_tail'], 'CAP_DATA', 0.10)
J9 = json.load(open('scratch/work/au/journey_au9_CLK.json'))
runs = []
for run in J9['runs']:
    pts = [tuple(p) for p in run['pts']]
    if run['layer'] == 1 and len(pts) == 2:
        continue  # old entry In2 stub - dropped
    if run['layer'] == 2 and pts[0] == (70.0, 1.8):
        i = pts.index((69.55, 2.7))
        runs.append(dict(layer=2, pts=[list(p) for p in pts[i:]]))
    else:
        runs.append(run)
CLK9T = dict(vias=J9['vias'], runs=runs)
add_new('clk9', CLK9T, 'CAP_CLK', 0.10)
print('model assembled', flush=True)


def item_margin(l, it, others):
    net = it[1]
    d = it[2]
    if it[0] == 'seg':
        m, _ = L.seg_margin(l, (d[0], d[1]), (d[2], d[3]), net, d[4],
                            [o for o in others if o[1] != net])
        return m
    if it[0] == 'via':
        m, _ = L.pt_margin(l, d[0], d[1], net, d[2],
                           [o for o in others if o[1] != net])
        return m
    return 9.9


# ---- conflict rips ----
TARGETS = {'PG_3V3': (54.0, 74.0, -18.0, 18.0),
           '+3V3D': (66.0, 78.0, 16.0, 28.0),
           'XO': (64.0, 78.0, 14.0, 24.0)}
RIP2 = {net: [] for net in TARGETS}
for net, (bx0, bx1, by0, by1) in TARGETS.items():
    seen = set()
    for l in range(3):
        cand = [it for it in pool[l] if it[1] == net
                and bx0 < C(it)[0] < bx1 and by0 < C(it)[1] < by1]
        for nit in NEW[l]:
            ncx, ncy = C(nit)
            if not (bx0 - 2 < ncx < bx1 + 2 and by0 - 2 < ncy < by1 + 2):
                continue
            for it in cand:
                key = (l, it[0], it[2])
                if key in seen:
                    continue
                if item_margin(l, nit, [it]) < 0:
                    seen.add(key)
                    RIP2[net].append(it)
    print(f'{net}: rip {len(RIP2[net])} items', flush=True)
for net, lst in RIP2.items():
    for it in lst:
        for l in range(3):
            if it in pool[l]:
                pool[l].remove(it)

# ---- generic multi-layer A* over a box ----
def make_astar(box, step):
    X0, X1, Y0, Y1 = box
    xs = np.arange(X0, X1 + 1e-9, step)
    ys = np.arange(Y0, Y1 + 1e-9, step)
    GXm, GYm = np.meshgrid(xs, ys)
    NYm, NXm = GXm.shape

    def df(it):
        kind, d = it[0], it[2]
        if kind == 'pad':
            cx, cy, hw, hh, rot = d
            dx, dy = GXm - cx, GYm - cy
            c, s = math.cos(-rot), math.sin(-rot)
            lx, ly = dx * c - dy * s, dx * s + dy * c
            return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                            np.maximum(np.abs(ly) - hh, 0.0))
        if kind == 'seg':
            x1, y1, x2, y2, hw = d
            px, py = GXm - x1, GYm - y1
            dx, dy = x2 - x1, y2 - y1
            L2 = dx * dx + dy * dy
            t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2,
                                            0, 1)
            return np.hypot(px - t * dx, py - t * dy) - hw
        return np.hypot(GXm - d[0], GYm - d[1]) - d[2]

    def bb(it):
        kind, d = it[0], it[2]
        if kind == 'pad':
            r = math.hypot(d[2], d[3])
            return d[0] - r, d[0] + r, d[1] - r, d[1] + r
        if kind == 'seg':
            return (min(d[0], d[2]) - d[4], max(d[0], d[2]) + d[4],
                    min(d[1], d[3]) - d[4], max(d[1], d[3]) + d[4])
        return d[0] - d[2], d[0] + d[2], d[1] - d[2], d[1] + d[2]

    def astar(net, start, goal, hw=0.10, layer_lock=None):
        myclr = netclass(net)[1]
        G = {}
        for l in range(3):
            f = np.full(GXm.shape, 9.9)
            for it in pool[l]:
                if it[1] == net:
                    continue
                a, b, c2, d2 = bb(it)
                req = max(myclr, it[3])
                if b < X0 - req - 0.3 or a > X1 + req + 0.3 or \
                   d2 < Y0 - req - 0.3 or c2 > Y1 + req + 0.3:
                    continue
                f = np.minimum(f, df(it) - req)
            G[l] = f
        track = {l: G[l] >= hw for l in range(3)}
        if layer_lock:
            for l in range(3):
                if not layer_lock[l]:
                    track[l] = np.zeros(GXm.shape, dtype=bool)
        viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25

        def cell(x, y):
            return (int(round((y - Y0) / step)),
                    int(round((x - X0) / step)))
        sc = cell(start[1], start[2])
        tc = cell(goal[1], goal[2])

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
                    if not (0 <= jy < NYm and 0 <= jx < NXm):
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
                vias.append((float(xs[cur[-1][2]]),
                             float(ys[cur[-1][1]])))
                cur = [p]
        runs.append(cur)
        o = dict(vias=[[round(a, 3), round(b, 3)] for a, b in vias],
                 runs=[])
        for run in runs:
            pp = [(float(xs[q[2]]), float(ys[q[1]])) for q in run]
            o['runs'].append(dict(layer=int(run[0][0]),
                                  pts=[[round(a, 3), round(b, 3)]
                                       for a, b in pp]))
        return o
    return astar


# ---- fragments + detours ----
def fragments(net, box):
    bx0, bx1, by0, by1 = box
    its = []
    for l in range(3):
        for it in pool[l]:
            if it[1] != net:
                continue
            cx, cy = C(it)
            if bx0 - 3 < cx < bx1 + 3 and by0 - 3 < cy < by1 + 3:
                its.append((l, it))
    parent = list(range(len(its)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    def endpoints(l, it):
        d = it[2]
        if it[0] == 'seg':
            return [(d[0], d[1]), (d[2], d[3])]
        return [(d[0], d[1])]
    pts = []
    for i, (l, it) in enumerate(its):
        for p in endpoints(l, it):
            pts.append((p, i, l))
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            (p1, a, l1), (p2, b, l2) = pts[i], pts[j]
            if a == b:
                continue
            if math.hypot(p1[0] - p2[0], p1[1] - p2[1]) < 0.02:
                union(a, b)
    frags = {}
    for i, (l, it) in enumerate(its):
        frags.setdefault(find(i), []).append(i)
    out = []
    for root, idxs in frags.items():
        terms = []
        for i in idxs:
            l, it = its[i]
            for p in endpoints(l, it):
                deg = sum(1 for (q, j, l2) in pts
                          if j != i and l2 == l
                          and math.hypot(p[0] - q[0], p[1] - q[1]) < 0.02)
                if deg == 0:
                    terms.append((l, p))
        out.append(dict(items=[its[i] for i in idxs], terms=terms))
    return out


def detour(net, box, hw, layer_lock=None, step=0.05):
    astar = make_astar(box, step)
    n = 0
    while True:
        fr = fragments(net, box)
        if len(fr) <= 1:
            print(f'  {net}: connected ({len(fr)} fragment)', flush=True)
            return True
        # closest terminal pair across fragments
        best = None
        for i in range(len(fr)):
            for j in range(i + 1, len(fr)):
                for (l1, p1) in fr[i]['terms']:
                    for (l2, p2) in fr[j]['terms']:
                        d = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                        if best is None or d < best[0]:
                            best = (d, (l1, p1), (l2, p2))
        if best is None:
            print(f'  {net}: fragments without terminals!', flush=True)
            return False
        _, (l1, p1), (l2, p2) = best
        starts = (l1,) if layer_lock else (0, 1, 2)
        J = astar(net, (starts, p1[0], p1[1]), (l2, p2[0], p2[1]),
                  hw=hw, layer_lock=layer_lock)
        if J is None:
            print(f'  {net}: detour NONE {p1} -> {p2}', flush=True)
            return False
        n += 1
        name = f'detour_{net}_{n}'
        add_new(name, J, net, hw)
        print(f'  {net}: detour {n} {p1} -> {p2} vias={J["vias"]}',
              flush=True)
        if n > 12:
            print(f'  {net}: too many detours', flush=True)
            return False


print('PG detours:', flush=True)
detour('PG_3V3', (54.0, 74.0, -18.0, 18.0), 0.125,
       layer_lock=(False, False, True))
print('+3V3D detours:', flush=True)
detour('+3V3D', (66.0, 78.0, 16.0, 28.0), 0.15, step=0.025)
print('XO detours:', flush=True)
detour('XO', (64.0, 78.0, 14.0, 24.0), 0.10,
       layer_lock=(False, True, False), step=0.025)

# fanout + heal2 retries in final model
astarF = make_astar((66.0, 72.5, -0.5, 6.0), 0.025)
J = astarF('I2C_SCL', ((0, 1, 2), 69.35, 1.40), (0, 66.2, 2.08), hw=0.10)
print('SCL fanout final:', 'FOUND' if J else 'NONE', flush=True)
if J:
    add_new('scl_ffan', J, 'I2C_SCL', 0.10)
J = astarF('+3V3A', ((0, 1, 2), 71.375, 0.875), (0, 69.125, 4.375),
           hw=0.10)
print('heal2 final:', 'FOUND' if J else 'NONE', flush=True)
if J:
    add_new('v3a_heal2', J, '+3V3A', 0.10)

# ---- FULL exact gate of every NEW item vs final pool ----
bad = 0
for l in range(3):
    others = [o for o in pool[l]]
    for nit in NEW[l]:
        m = item_margin(l, nit, others)
        if m < -0.001:
            bad += 1
            print(f'GATE FAIL L{l} {m:+.3f} NEW {L.fmt_it(nit)}',
                  flush=True)
print(f'full gate: {bad} failures', flush=True)

json.dump(dict(
    journeys=JOURNEYS,
    fixed={str(l): [[it[0], it[1], list(it[2]), it[3]] for it in FIXED[l]]
           for l in range(3)},
    rip2={net: [[it[0], it[1], list(it[2]), it[3]] for it in lst]
          for net, lst in RIP2.items()},
    clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25),
    open('scratch/work/au/build_au71.json', 'w'))
print('saved build_au71.json', flush=True)
print('done', flush=True)
