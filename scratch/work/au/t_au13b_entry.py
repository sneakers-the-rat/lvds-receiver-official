"""t_au13b: DATA entry re-plan (ablation variants). Fine grid (0.025) 3-layer A* in box
x[62.5,71.5] y[-0.5,13.5], fields from the settled model + CLK9 items.
Start: any layer at DATA esc via (69.9,3.18). Goal: In2 at DATA30's
ride point nearest (65.3,4.6). Then splice + full exact check."""
import sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
import t_au1_lib as U
import t_ai_lib as L
import pcbnew
from router import netclass

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items_full = L.load_items(board)
PG_PRED = lambda l, it: l == 2 and it[1] == 'PG_3V3' \
    and 60 < U.item_centre(it)[0] < 70 and 0 < U.item_centre(it)[1] < 16
P3F_PRED = lambda l, it: l == 0 and it[1] == '+3V3D' \
    and it[0] in ('seg', 'via') \
    and 68 < U.item_centre(it)[0] < 77 and 19 < U.item_centre(it)[1] < 27
XO_PRED = lambda l, it: l == 1 and it[1] == 'XO' \
    and 66 < U.item_centre(it)[0] < 76 and 16 < U.item_centre(it)[1] < 23
import os
EXTRA = os.environ.get('EXTRA_ABL', '')
PREDS = {
    'THR66': lambda l, it: it[0] == 'via' and it[1] == 'THR_DAC'
        and abs(it[2][0] - 66.625) < 0.1 and abs(it[2][1] - 4.875) < 0.1,
    'GND67': lambda l, it: it[0] == 'via' and it[1] == 'GND'
        and abs(it[2][0] - 67.375) < 0.1 and abs(it[2][1] - 4.125) < 0.1,
    'SCLDIAG': lambda l, it: l == 1 and it[1] == 'I2C_SCL'
        and it[0] == 'seg' and abs(it[2][0] - 67.875) < 0.01
        and abs(it[2][1] - 5.125) < 0.01,
    'P3V3AVIA': lambda l, it: it[0] == 'via' and it[1] == '+3V3A'
        and abs(it[2][0] - 69.125) < 0.1 and abs(it[2][1] - 4.375) < 0.1,
}
xp = [PREDS[n] for n in EXTRA.split(',') if n]
pool = {l: [it for it in items_full[l] if not PG_PRED(l, it)
            and not P3F_PRED(l, it) and not XO_PRED(l, it)
            and not any(p(l, it) for p in xp)]
        for l in range(3)}
print('EXTRA_ABL =', EXTRA, flush=True)
clk_items = U.journey_items('scratch/work/au/journey_au9_CLK.json',
                            'CAP_CLK')
union = {l: pool[l] + clk_items[l] for l in range(3)}

J30 = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
run0 = J30['runs'][0]
pts0 = [tuple(p) for p in run0['pts']]
cand = min(range(len(pts0)),
           key=lambda i: math.hypot(pts0[i][0] - 65.3, pts0[i][1] - 4.6))
REJOIN = pts0[cand]
print(f'rejoin at idx {cand}: {REJOIN}', flush=True)

# fine grid
FX0, FX1, FY0, FY1, FST = 62.5, 71.5, -0.5, 13.5, 0.025
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


G = {}
myclr = netclass('CAP_DATA')[1]
for l in range(3):
    f = np.full(FGX.shape, 9.9)
    for it in union[l]:
        if it[1] == 'CAP_DATA':
            continue
        bx0, bx1, by0, by1 = bbox(it)
        req = max(myclr, it[3])
        if bx1 < FX0 - req - 0.3 or bx0 > FX1 + req + 0.3 or \
           by1 < FY0 - req - 0.3 or by0 > FY1 + req + 0.3:
            continue
        f = np.minimum(f, dist_field(it) - req)
    G[l] = f
print('fine fields built', flush=True)


def fcell(x, y):
    return (int(round((y - FY0) / FST)), int(round((x - FX0) / FST)))


track = {l: G[l] >= 0.10 for l in range(3)}
viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
sc = fcell(69.9, 3.18)
tc = fcell(*REJOIN)


def h(p):
    return math.hypot(p[1] - tc[0], p[2] - tc[1])


openh = []
came = {}
gs = {}
for l in range(3):
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
    if l == 1 and (iy, ix) == tc:
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
print(f'entry A*: {"FOUND" if goalp else "NONE"}', flush=True)
if goalp:
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
    entry = dict(vias=[[round(a, 3), round(b, 3)] for a, b in vias],
                 runs=[])
    for run in runs:
        pp = [(float(fxs[q[2]]), float(fys[q[1]])) for q in run]
        entry['runs'].append(dict(layer=int(run[0][0]),
                                  pts=[[round(a, 3), round(b, 3)]
                                       for a, b in pp]))
    print(f'entry vias: {entry["vias"]}', flush=True)
    for r in entry['runs']:
        print(f'   L{r["layer"]}: {r["pts"][0]} -> {r["pts"][-1]} '
              f'({len(r["pts"])} pts)', flush=True)
    json.dump(entry, open('scratch/work/au/entry_au13_DATA.json', 'w'))
    # splice: entry runs + DATA30 remainder from rejoin idx
    rem = [list(p) for p in pts0[cand:]]
    full_runs = entry['runs'][:-1]
    last = entry['runs'][-1]
    merged = dict(layer=1, pts=last['pts'] + rem[1:])
    full_runs.append(merged)
    full_runs += [dict(layer=r['layer'], pts=r['pts'])
                  for r in J30['runs'][1:]]
    full = dict(net='CAP_DATA',
                vias=entry['vias'] + J30['vias'], runs=full_runs)
    json.dump(full, open('scratch/work/au/journey_au13_DATA.json', 'w'))
    print('spliced journey written', flush=True)
print('done', flush=True)
