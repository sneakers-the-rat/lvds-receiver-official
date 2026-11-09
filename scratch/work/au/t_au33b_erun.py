"""t_au33b: SCL In2 E-run attempt on F(+B) from pocket via (69.35,1.40) to
the chain component's F stub at R20 (69.675,12.75), in the au30
model (pocket rebuilt, frag bowed, DATA entry placed). Box y to 14."""
import wx
_app = wx.App(False)
import sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
src = open('scratch/work/au/t_au30_chain.py').read()
head = src.split('# ---- fine A* machinery')[0]
g = {'__name__': 'chaindata'}
exec(head, g)
pool = g['pool']
jd = json.load(open('scratch/work/au/entry_au30_DATA.json'))
items = g['journey_items_dense'](jd, 'CAP_DATA')
for l in range(3):
    pool[l] += items[l]

FX0, FX1, FY0, FY1, FST = 62.0, 80.0, -1.0, 14.0, 0.025
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


from router import netclass


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
                step = 1.414 if dx and dy else 1.0
                pen = max(0.0, 0.55 - G[l][jy, jx]) * 6.0
                ng = gg + step + pen
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
    out = dict(vias=[[round(a, 3), round(b, 3)] for a, b in vias], runs=[])
    for run in runs:
        pp = [(float(fxs[q[2]]), float(fys[q[1]])) for q in run]
        out['runs'].append(dict(layer=int(run[0][0]),
                                pts=[[round(a, 3), round(b, 3)]
                                     for a, b in pp]))
    return out


J = astar('I2C_SCL', ((1,), 69.625, 12.625), (1, 78.125, 8.375))
if J is None:
    print('SCL In2 E-run: NONE')
else:
    print('SCL In2 E-run: FOUND vias=', J['vias'])
    for r in J['runs']:
        print(f"   L{r['layer']}: {r['pts'][0]} -> {r['pts'][-1]} "
              f"({len(r['pts'])} pts)")
    json.dump(J, open('scratch/work/au/erun_au33_SCL.json', 'w'))
print('done')
