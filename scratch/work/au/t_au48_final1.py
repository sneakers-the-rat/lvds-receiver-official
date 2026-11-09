"""t_au48: final phase-1 assembly. Order: bheal+hop, heal1 F-ONLY,
exit (goals (69.55,2.7) then (69.4,2.8)), DATA entry + tail,
heal2. Saves heals_au48.json."""
import wx
_app = wx.App(False)
import sys, json, math, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au43_phase1b.py').read()
exec(src.split("J40 = json.load")[0], g)
exec(src[src.index("def entry_astar"):src.index("out = {}")], g)
exec(src[src.index("FBOX ="):src.index("J = fastest('+3V3A'")], g)
pool = g['pool']
entry_astar = g['entry_astar']
journey_items_dense = g['journey_items_dense']
build_G = g['build_G']
fcell = g['fcell']
fxs, fys = g['fxs'], g['fys']
FNY, FNX = g['FNY'], g['FNX']


def run_astar(net, start, goal, hw=0.10, allow_via=True):
    G = build_G(net)
    track = {l: G[l] >= hw for l in range(3)}
    if allow_via:
        viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
    else:
        viafit = np.zeros(G[0].shape, dtype=bool)
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


def add_j(J, net, hw=0.10):
    for l, its in journey_items_dense(J, net, hw=hw).items():
        pool[l] += its


J40 = json.load(open('scratch/work/au/joint_au40.json'))
for nm in ('bheal', 'hop'):
    J = J40['jobs'][nm]
    net = {'bheal': 'I2C_SCL', 'hop': 'I2C_SDA'}[nm]
    hw = 0.125 if nm == 'hop' else 0.10
    add_j(J, net, hw)
out = {}
J = run_astar('+3V3A', ((0,), 68.225, 2.75), (0, 69.125, 4.375),
              hw=0.10, allow_via=False)
print('heal1 F-only:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['v3a_heal1'] = J
    add_j(J, '+3V3A', 0.10)
exitJ = None
for goal in ((69.55, 2.70), (69.4, 2.8)):
    J = run_astar('CAP_CLK', ((0, 1, 2), 70.2, 1.8), (2, goal[0], goal[1]))
    print(f'exit -> {goal}:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        exitJ = J
        out['clk_exit'] = J
        out['clk_rejoin'] = goal
        add_j(J, 'CAP_CLK', 0.10)
        break
J = entry_astar('CAP_DATA', 1, 69.9, 3.175, 63.85, 6.3,
                (60.0, 72.0, -1.0, 10.0))
print('DATA entry:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['data_entry'] = J
    add_j(J, 'CAP_DATA')
    J30 = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
    pts0 = J30['runs'][0]['pts']
    TAIL = dict(vias=J30['vias'],
                runs=[dict(layer=1, pts=pts0[213:])] + J30['runs'][1:])
    out['data_tail'] = TAIL
    add_j(TAIL, 'CAP_DATA')
J = run_astar('+3V3A', ((0,), 71.375, 0.875), (0, 69.125, 4.375),
              hw=0.10)
print('heal2:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['v3a_heal2'] = J
json.dump(out, open('scratch/work/au/heals_au48.json', 'w'))
print('done', flush=True)
