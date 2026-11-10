"""t_au37: assemble the FULL final CAP model and heal the remaining
webs. Base: esc pool + pocket rips (au30, incl frag bow, U9 west,
NO PG/P3F/XO ablation) + CLK9 + DATA(entry30 + DATA30 tail) + SCL
fanout + SCL long heal - SCL B staircase. Then: conflict-rip PG B /
+3V3D F / XO In2 items vs the new copper, and A* the heals:
+3V3A x2 (F), PG gaps (B), +3V3D gaps (F), XO gaps (In2).
Outputs heal journey JSONs + a build manifest."""
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

src = open('scratch/work/au/t_au30_chain.py').read()
head = src.split('PG_PRED =')[0]  # up to ablation preds
g = {'__name__': 'au30head'}
exec(head, g)
items_full = g['items_full']
RIPS = g['RIPS']
U9PADS = g['U9PADS']
C = U.item_centre

# staircase rip: all SCL B segs (the 28-seg staircase is the only SCL
# B chain in x[70,79] y[2,10]; exclude vias and far items by box)
STAIR = lambda l, it: l == 2 and it[1] == 'I2C_SCL' and it[0] == 'seg' \
    and 70.5 < C(it)[0] < 78.5 and 2.0 < C(it)[1] < 9.5
RIPS.append(STAIR)
pool = {l: [it for it in items_full[l]
            if not any(p(l, it) for p in RIPS)] for l in range(3)}
nstair = sum(1 for it in items_full[2] if STAIR(2, it))
print(f'staircase segs ripped: {nstair}', flush=True)
for it in U9PADS:
    d = it[2]
    pool[0].append(('pad', it[1], (d[0] - 1.0, d[1], d[2], d[3], d[4]),
                    it[3]))
NEW = g['NEW']
for l in range(3):
    pool[l] += NEW[l]

journey_items_dense = g['journey_items_dense']
clk_items = g['clk_items']
for l in range(3):
    pool[l] += clk_items[l]
jd = json.load(open('scratch/work/au/entry_au30_DATA.json'))
for l in range(3):
    pool[l] += journey_items_dense(jd, 'CAP_DATA')[l]
# DATA30 tail from rejoin idx213
J30 = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
pts0 = J30['runs'][0]['pts']
tail = dict(net='CAP_DATA', vias=J30['vias'],
            runs=[dict(layer=1, pts=pts0[213:])] + J30['runs'][1:])
for l in range(3):
    pool[l] += journey_items_dense(tail, 'CAP_DATA')[l]
jf = json.load(open('scratch/work/au/ffan_au30_SCL.json'))
for l in range(3):
    pool[l] += journey_items_dense(jf, 'I2C_SCL')[l]
jh = json.load(open('scratch/work/au/fheal_au33_SCL.json'))
for l in range(3):
    pool[l] += journey_items_dense(jh, 'I2C_SCL')[l]

NEWJ = []  # (net, items) of everything added over esc
for nm, it in (('CAP_CLK', clk_items),):
    NEWJ.append((nm, it))

# ---------- conflict analysis ----------
def item_margin(l, it, others):
    """min margin of item it (on layer l) vs list others (same layer)."""
    kind, net, d, clr = it
    worst = 9.9
    if kind == 'seg':
        m, _ = L.seg_margin(l, (d[0], d[1]), (d[2], d[3]), net, d[4],
                            [o for o in others if o[1] != net])
        worst = m
    elif kind == 'via':
        m, _ = U.pt_margin(l, d[0], d[1], net, d[2],
                           [o for o in others if o[1] != net])
        worst = m
    return worst


def journey_flat(J):
    out = []
    items = journey_items_dense(J, 'X')
    for l in range(3):
        out += [(l, it) for it in items[l]]
    return out


added = []
added += [(l, it) for l in range(3) for it in clk_items[l]]
added += [(l, it) for l in range(3)
          for it in journey_items_dense(jd, 'CAP_DATA')[l]]
added += [(l, it) for l in range(3)
          for it in journey_items_dense(tail, 'CAP_DATA')[l]]
added += [(l, it) for l in range(3)
          for it in journey_items_dense(jf, 'I2C_SCL')[l]]
added += [(l, it) for l in range(3)
          for it in journey_items_dense(jh, 'I2C_SCL')[l]]

TARGETS = {
    'PG_3V3': (2, (54, 76, -17, 28)),
    '+3V3D': (0, (68, 77, 19, 27)),
    'XO': (1, (66, 76, 16, 23)),
}
rip_extra = []
for net, (l, box) in TARGETS.items():
    others = [it for (ll, it) in added if ll == l]
    for it in list(pool[l]):
        if it[1] != net or it[0] == 'pad':
            continue
        c = C(it)
        if not (box[0] < c[0] < box[1] and box[2] < c[1] < box[3]):
            continue
        m = item_margin(l, it, others)
        if m < 0.02:
            rip_extra.append((l, it))
            pool[l].remove(it)
            print(f'conflict-rip L{l} {net} margin {m:+.3f}: '
                  f'{L.fmt_it(it)}', flush=True)
print(f'conflict rips: {len(rip_extra)}', flush=True)

# ---------- A* machinery (per-call box) ----------
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


def add_j(J, net):
    items = journey_items_dense(J, net)
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
# +3V3A heals (F, pocket box, fine grid)
astarA = make_astar((66.0, 72.5, -0.5, 6.0), 0.025)
J = astarA('+3V3A', ((0,), 68.225, 2.75), (0, 69.125, 4.375), hw=0.15)
if show('+3V3A heal1 (U9 pad -> G3 via)', J):
    add_j(J, '+3V3A')
    heals['p3a_1'] = J
J = astarA('+3V3A', ((0,), 71.375, 0.875), (0, 69.125, 4.375), hw=0.15)
if show('+3V3A heal2 (U6 stub -> G3 via)', J):
    add_j(J, '+3V3A')
    heals['p3a_2'] = J

# PG gaps: find chain fragments after conflict rips
def chain_gaps(net, layer):
    """boundary joints: seg endpoints of net on layer that coincide
    with a ripped item's endpoint — approximate: endpoints whose
    degree within kept items == 1 and that lie inside the region
    where rips happened."""
    from collections import Counter
    deg = Counter()
    for it in pool[layer]:
        if it[1] == net and it[0] == 'seg':
            d = it[2]
            deg[(round(d[0], 3), round(d[1], 3))] += 1
            deg[(round(d[2], 3), round(d[3], 3))] += 1
    return [p for p, n in deg.items() if n == 1]


pg_ends = chain_gaps('PG_3V3', 2)
print('PG open ends:', pg_ends, flush=True)
astarPG = make_astar((54.0, 72.0, -2.0, 17.0), 0.05)
# pair up ends greedily by distance (chain order unknown; try pairs)
ends = list(pg_ends)
tried = 0
while len(ends) >= 2 and tried < 6:
    a = ends[0]
    # nearest other end
    b = min(ends[1:], key=lambda p: math.hypot(p[0] - a[0], p[1] - a[1]))
    J = astarPG('PG_3V3', ((2,), a[0], a[1]), (2, b[0], b[1]), hw=0.125)
    if show(f'PG detour {a}->{b}', J):
        add_j(J, 'PG_3V3')
        heals[f'pg_{tried}'] = J
        ends.remove(a)
        ends.remove(b)
    else:
        ends.remove(a)
        ends.append(a)
    tried += 1
print('PG ends left:', ends, flush=True)

# +3V3D gaps in U5 box
p3_ends = [p for p in chain_gaps('+3V3D', 0)
           if 68 < p[0] < 77 and 19 < p[1] < 27]
print('+3V3D open ends in box:', p3_ends, flush=True)
astarP3 = make_astar((67.0, 78.0, 18.0, 28.0), 0.025)
ends = list(p3_ends)
tried = 0
while len(ends) >= 2 and tried < 4:
    a = ends[0]
    b = min(ends[1:], key=lambda p: math.hypot(p[0] - a[0], p[1] - a[1]))
    J = astarP3('+3V3D', ((0,), a[0], a[1]), (0, b[0], b[1]), hw=0.15)
    if show(f'+3V3D heal {a}->{b}', J):
        add_j(J, '+3V3D')
        heals[f'p3d_{tried}'] = J
        ends.remove(a)
        ends.remove(b)
    else:
        ends.remove(a)
        ends.append(a)
    tried += 1
print('+3V3D ends left:', ends, flush=True)

# XO gaps in box
xo_ends = [p for p in chain_gaps('XO', 1)
           if 66 < p[0] < 76 and 16 < p[1] < 23]
print('XO open ends in box:', xo_ends, flush=True)
astarXO = make_astar((65.0, 77.0, 15.0, 24.0), 0.025)
ends = list(xo_ends)
tried = 0
while len(ends) >= 2 and tried < 4:
    a = ends[0]
    b = min(ends[1:], key=lambda p: math.hypot(p[0] - a[0], p[1] - a[1]))
    J = astarXO('XO', ((1,), a[0], a[1]), (1, b[0], b[1]))
    if show(f'XO heal {a}->{b}', J):
        add_j(J, 'XO')
        heals[f'xo_{tried}'] = J
        ends.remove(a)
        ends.remove(b)
    else:
        ends.remove(a)
        ends.append(a)
    tried += 1
print('XO ends left:', ends, flush=True)

json.dump(heals, open('scratch/work/au/heals_au37.json', 'w'))
json.dump([f'L{l} {it[1]} {it[0]} {it[2]}' for (l, it) in rip_extra],
          open('scratch/work/au/conflict_rips_au37.json', 'w'))
print('done', flush=True)
