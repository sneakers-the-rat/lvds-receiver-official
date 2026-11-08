"""t_au2: combination ablations + sequential feasibility A*.
Usage: t_au2_pairs.py A|B combo1,combo2,...
Direction A: sibling CLK (journey32) fixed, DATA measured.
Direction B: sibling DATA (journey30) fixed, CLK measured.
For each combo: widest bottleneck; if >= -0.01 also run sequential
A* (sibling fixed as items, target net free) and print the journey."""
import sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
import t_au1_lib as U
import t_ai_lib as L

mode = sys.argv[1]
combos = sys.argv[2].split(',')
if mode == 'A':
    sib_net, net = 'CAP_CLK', 'CAP_DATA'
    sib_file = 'scratch/work/as/journey32_CAP_CLK_CD.json'
else:
    sib_net, net = 'CAP_DATA', 'CAP_CLK'
    sib_file = 'scratch/work/as/journey30_CAP_DATA_DC.json'

GROUPS = {
    'PG': lambda l, it: l == 2 and it[1] == 'PG_3V3'
        and 60 < U.item_centre(it)[0] < 70 and 0 < U.item_centre(it)[1] < 16,
    'SCL': lambda l, it: l == 1 and it[1] == 'I2C_SCL'
        and 62 < U.item_centre(it)[0] < 72 and -1 < U.item_centre(it)[1] < 10,
    'THR66': lambda l, it: it[0] == 'via' and abs(it[2][0] - 66.625) < 0.1
        and abs(it[2][1] - 4.875) < 0.1,
    'HVREST': lambda l, it: l == 1 and it[1] == 'HV_SHDN',
    'P3V3A_VIA': lambda l, it: it[0] == 'via'
        and abs(it[2][0] - 69.125) < 0.1 and abs(it[2][1] - 4.375) < 0.1,
}


def astar(G, net):
    track = {l: G[l] >= 0.10 for l in range(3)}
    viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
    case = U.CASES[net]
    sc = U.cell(*case['start'])
    tc = U.cell(*case['target'])

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
                if not (0 <= jy < U.NY and 0 <= jx < U.NX):
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
    if goal is None:
        return None
    path = []
    p = goal
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
            vias.append((float(U.xs[cur[-1][2]]), float(U.ys[cur[-1][1]])))
            cur = [p]
    runs.append(cur)
    out = dict(net=net, vias=[[round(a, 3), round(b, 3)] for a, b in vias],
               runs=[])
    for run in runs:
        pts = [(float(U.xs[p[2]]), float(U.ys[p[1]])) for p in run]
        out['runs'].append(dict(layer=int(run[0][0]),
                                pts=[[round(a, 3), round(b, 3)]
                                     for a, b in pts]))
    return out


pool = U.load_pool()
sib = U.journey_items(sib_file, sib_net)

for combo in combos:
    names = combo.split('+')
    preds = [GROUPS[n] for n in names]
    comb = {l: [it for it in pool[l]
                if not any(p(l, it) for p in preds)] for l in range(3)}
    n_removed = sum(len(pool[l]) - len(comb[l]) for l in range(3))
    for l in range(3):
        comb[l] += sib[l]
    G = {}
    for l in range(3):
        G[l], _, _ = U.build_field(comb[l], net)
    bv, _, _ = U.widest(G, net)
    print(f'== {mode} combo {combo} ({n_removed} items out): '
          f'{net} widest {bv:+.3f}', flush=True)
    if bv >= -0.01:
        J = astar(G, net)
        print(f'   A* journey: {"FOUND" if J else "NONE"}', flush=True)
        if J:
            fn = (f'scratch/work/au/journey_au2_{net}_{mode}_'
                  f'{"_".join(names)}.json')
            json.dump(J, open(fn, 'w'))
            print(f'   vias: {J["vias"]}', flush=True)
            for r in J['runs']:
                print(f'   L{r["layer"]}: {r["pts"][0]} -> {r["pts"][-1]} '
                      f'({len(r["pts"])} pts)', flush=True)
            print(f'   wrote {fn}', flush=True)
print('done', flush=True)
