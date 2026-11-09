"""t_au72: phase 2c - fixes from au71 gate:
- hop re-run with exit via (69.075,2.8) as fence
- DATA tail In2 run re-planned with CLK9 as fence
- detours: multi-layer PG, XO box y8, all-pairs fallback
- full gate + fragment counts. Saves build_au73.json."""
import wx
_app = wx.App(False)
import sys, json, math, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2c'}
src71 = open('scratch/work/au/t_au71_phase2b.py').read()
# exec au71 up to its model assembly (before conflict rips), but we
# need our own assembly: split at the FIXED application end marker
head = src71.split("# ---- conflict rips ----")[0]
# head includes au71's own add_new calls (bheal/hop/old exit/data/
# clk9). We want the base only: split earlier, at "NEW = {"
base = src71.split("NEW = {")[0]
exec(base, g)
pool = g['pool']
journey_items_dense = g['journey_items_dense']
seg_ = g['seg_']
via_ = g['via_']
C = g['C']
item_margin = None
import t_ai_lib as L
from router import netclass


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


NEW = {0: [], 1: [], 2: []}
JOURNEYS = {}


def add_new(name, J, net, hw=0.10):
    JOURNEYS[name] = J
    for l, its in journey_items_dense(J, net, hw=hw).items():
        NEW[l] += its
        pool[l] += its


# generic A* (same as au71's make_astar, re-created here on pool)
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


astarPocket = make_astar((66.0, 72.5, -0.5, 6.0), 0.025)
astarNE = make_astar((60.0, 78.0, 10.0, 28.0), 0.025)
J40 = json.load(open('scratch/work/au/joint_au40.json'))
add_new('bheal', J40['jobs']['bheal'], 'I2C_SCL', 0.10)
# exit via as fence BEFORE hop
for l in range(3):
    it = ('via', 'CAP_CLK', (69.075, 2.8, 0.25), 0.2)
    NEW[l].append(it)
    pool[l].append(it)
J = astarPocket('I2C_SDA', ((0, 1, 2), 69.05, 2.05), (1, 71.125, 1.875),
                hw=0.125)
print('hop re-run (exit via fenced):', 'FOUND' if J else 'NONE',
      flush=True)
if J:
    add_new('hop', J, 'I2C_SDA', 0.125)
J67 = json.load(open('scratch/work/au/heals_au67.json'))
add_new('v3a_heal1', J67['v3a_heal1'], '+3V3A', 0.10)
add_new('clk_exit_frun', J67['clk_exit_frun'], 'CAP_CLK', 0.10)
bj = ('seg', 'CAP_CLK', (69.075, 2.8, 69.55, 2.7, 0.10), 0.2)
NEW[2].append(bj)
pool[2].append(bj)
add_new('data_entry', J67['data_entry'], 'CAP_DATA', 0.10)
# CLK9 before DATA tail re-plan
J9 = json.load(open('scratch/work/au/journey_au9_CLK.json'))
runs = []
for run in J9['runs']:
    pts = [tuple(p) for p in run['pts']]
    if run['layer'] == 1 and len(pts) == 2:
        continue
    if run['layer'] == 2 and pts[0] == (70.0, 1.8):
        i = pts.index((69.55, 2.7))
        runs.append(dict(layer=2, pts=[list(p) for p in pts[i:]]))
    else:
        runs.append(run)
CLK9T = dict(vias=J9['vias'], runs=runs)
add_new('clk9', CLK9T, 'CAP_CLK', 0.10)
# DATA tail: keep run0 tail + F hop + arrival runs; re-plan In2 run2
J30 = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
pts0 = J30['runs'][0]['pts']
J = astarNE('CAP_DATA', ((1,), 64.7, 15.45), (1, 72.6, 19.3), hw=0.10,
            layer_lock=(False, True, False))
mode = 'in2'
if J is None:
    J = astarNE('CAP_DATA', ((0, 1, 2), 64.7, 15.45), (1, 72.6, 19.3),
                hw=0.10)
    mode = 'multi'
print(f'DATA tail run2 re-plan ({mode}):', 'FOUND' if J else 'NONE',
      flush=True)
TAIL = dict(vias=J30['vias'],
            runs=[dict(layer=1, pts=pts0[213:]), J30['runs'][1],
                  J if J else J30['runs'][2], J30['runs'][3],
                  J30['runs'][4]])
add_new('data_tail', TAIL, 'CAP_DATA', 0.10)
print('model assembled', flush=True)

# ---- conflict rips (same as au71) ----
TARGETS = {'PG_3V3': (54.0, 74.0, -18.0, 18.0),
           '+3V3D': (66.0, 78.0, 16.0, 28.0),
           'XO': (64.0, 78.0, 8.0, 24.0)}
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

# ---- fragments + detours with pair fallback ----
exec(src71[src71.index("def fragments"):src71.index("def detour")],
     g)
fragments = g['fragments']


def detour2(net, box, hw, layer_lock=None, step=0.05):
    astar = make_astar(box, step)
    n = 0
    while True:
        fr = fragments(net, box)
        if len(fr) <= 1:
            print(f'  {net}: connected', flush=True)
            return True
        pairs = []
        for i in range(len(fr)):
            for j in range(i + 1, len(fr)):
                for (l1, p1) in fr[i]['terms']:
                    for (l2, p2) in fr[j]['terms']:
                        pairs.append((math.hypot(p1[0] - p2[0],
                                                  p1[1] - p2[1]),
                                      (l1, p1), (l2, p2)))
        pairs.sort()
        done = False
        for (_, (l1, p1), (l2, p2)) in pairs[:14]:
            starts = (l1,) if layer_lock else (0, 1, 2)
            J = astar(net, (starts, p1[0], p1[1]), (l2, p2[0], p2[1]),
                      hw=hw, layer_lock=layer_lock)
            if J is not None:
                n += 1
                add_new(f'detour_{net}_{n}', J, net, hw)
                print(f'  {net}: detour {n} {p1} -> {p2} '
                      f'vias={J["vias"]}', flush=True)
                done = True
                break
        if not done:
            print(f'  {net}: NO detour for {len(fr)} fragments',
                  flush=True)
            return False
        if n > 12:
            return False


print('PG detours:', flush=True)
detour2('PG_3V3', (54.0, 74.0, -18.0, 18.0), 0.125)
print('+3V3D detours:', flush=True)
detour2('+3V3D', (66.0, 78.0, 16.0, 28.0), 0.15, step=0.025)
print('XO detours:', flush=True)
detour2('XO', (64.0, 78.0, 8.0, 24.0), 0.10,
        layer_lock=(False, True, False), step=0.025)
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

bad = 0
for l in range(3):
    for nit in NEW[l]:
        m = item_margin(l, nit, pool[l])
        if m < -0.001:
            bad += 1
            if bad <= 15:
                print(f'GATE FAIL L{l} {m:+.3f} NEW {L.fmt_it(nit)}',
                      flush=True)
print(f'full gate: {bad} failures', flush=True)
for net, box in (('CAP_CLK', (55.0, 80.0, -2.0, 30.0)),
                 ('CAP_DATA', (55.0, 80.0, -2.0, 30.0)),
                 ('PG_3V3', (50.0, 78.0, -20.0, 30.0)),
                 ('+3V3D', (60.0, 80.0, 10.0, 30.0)),
                 ('XO', (60.0, 80.0, 5.0, 26.0)),
                 ('I2C_SCL', (60.0, 80.0, -2.0, 16.0)),
                 ('I2C_SDA', (60.0, 80.0, -2.0, 16.0)),
                 ('+3V3A', (60.0, 80.0, -2.0, 16.0))):
    fr = fragments(net, box)
    sizes = sorted((len(f['items']) for f in fr), reverse=True)
    print(f'fragments {net}: {len(fr)} sizes {sizes[:6]}', flush=True)
json.dump(dict(
    journeys=JOURNEYS,
    fixed={str(l): [[it[0], it[1], list(it[2]), it[3]]
                     for it in g['FIXED'][l]] for l in range(3)},
    rip2={net: [[it[0], it[1], list(it[2]), it[3]] for it in lst]
          for net, lst in RIP2.items()},
    clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25),
    open('scratch/work/au/build_au73.json', 'w'))
print('saved build_au73.json', flush=True)
print('done', flush=True)
