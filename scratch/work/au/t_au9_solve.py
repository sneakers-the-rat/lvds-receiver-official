"""t_au9: settle CLK arrival + DATA in the build model.
Models: base = full exp241esc - PG corridor - +3V3D F segs/vias in
U5 box. Variant B additionally removes XO In2 segs/vias in the
arrival box. Try variant A for the CLK arrival; fall back to B.
Then DATA A* with CLK fenced as items. Exact-check the pair against
the model pool (ablated webs excluded = the re-lay set)."""
import sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
import t_au1_lib as U
import t_ai_lib as L
import pcbnew

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items_full = L.load_items(board)

PG_PRED = lambda l, it: l == 2 and it[1] == 'PG_3V3' \
    and 60 < U.item_centre(it)[0] < 70 and 0 < U.item_centre(it)[1] < 16
P3F_PRED = lambda l, it: l == 0 and it[1] == '+3V3D' \
    and it[0] in ('seg', 'via') \
    and 68 < U.item_centre(it)[0] < 77 and 19 < U.item_centre(it)[1] < 27
XO_PRED = lambda l, it: l == 1 and it[1] == 'XO' \
    and 66 < U.item_centre(it)[0] < 76 and 16 < U.item_centre(it)[1] < 23


def mkpool(xo):
    return {l: [it for it in items_full[l] if not PG_PRED(l, it)
                and not P3F_PRED(l, it) and not (xo and XO_PRED(l, it))]
            for l in range(3)}


def astar(G, start, goal):
    track = {l: G[l] >= 0.10 for l in range(3)}
    viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
    sc = U.cell(start[1], start[2])
    tc = U.cell(goal[1], goal[2])

    def h(p):
        return math.hypot(p[1] - tc[0], p[2] - tc[1])
    s0 = (start[0], sc[0], sc[1])
    openh = [(h(s0), 0.0, s0)]
    came = {s0: None}
    gs = {s0: 0.0}
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
            vias.append((float(U.xs[cur[-1][2]]), float(U.ys[cur[-1][1]])))
            cur = [p]
    runs.append(cur)
    out = dict(vias=[[round(a, 3), round(b, 3)] for a, b in vias], runs=[])
    for run in runs:
        pts = [(float(U.xs[p[2]]), float(U.ys[p[1]])) for p in run]
        out['runs'].append(dict(layer=int(run[0][0]),
                                pts=[[round(a, 3), round(b, 3)]
                                     for a, b in pts]))
    return out


def fields(pool, net, extra=None):
    G = {}
    for l in range(3):
        lst = list(pool[l]) + (extra.get(l, []) if extra else [])
        G[l], _, _ = U.build_field(lst, net)
    return G


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


def check(J, net, pool, extra):
    union = {l: pool[l] + extra[l] for l in range(3)}
    worst = (9.9, None, None)
    for l in range(3):
        for it in J[l]:
            d = it[2]
            if it[0] == 'seg':
                box = (min(d[0], d[2]) - 2.2, max(d[0], d[2]) + 2.2,
                       min(d[1], d[3]) - 2.2, max(d[1], d[3]) + 2.2)
                local = L.in_box_pool(union, box, pad=0.6)
                m, w = L.seg_margin(l, (d[0], d[1]), (d[2], d[3]),
                                    net, 0.10, local[l])
            else:
                box = (d[0] - 2.2, d[0] + 2.2, d[1] - 2.2, d[1] + 2.2)
                local = L.in_box_pool(union, box, pad=0.6)
                m, w = L.pt_margin(l, d[0], d[1], net, 0.25, local[l])
            if m < worst[0]:
                worst = (m, it, w)
    return worst


J = json.load(open('scratch/work/au/journey_au2_CAP_CLK_B_PG.json'))
head_runs = []
for run in J['runs']:
    head_runs.append(run)
    if run['pts'][-1] == [64.75, 16.95]:
        break

CLKJ = None
for xo in (False, True):
    pool = mkpool(xo)
    G = fields(pool, 'CAP_CLK')
    arr = astar(G, (1, 64.75, 16.95), (0, 75.45, 25.385))
    print(f'CLK arrival (XO ablated={xo}): '
          f'{"FOUND" if arr else "NONE"}', flush=True)
    if arr is None:
        continue
    full = dict(net='CAP_CLK', vias=[[64.75, 16.95]] + arr['vias'],
                runs=head_runs + arr['runs'])
    items = journey_items_dense(full, 'CAP_CLK')
    w = check(items, 'CAP_CLK', pool, {0: [], 1: [], 2: []})
    print(f'   arrival vias {arr["vias"]}; exact worst {w[0]:+.3f} '
          f'({L.fmt_it(w[1])} vs {L.fmt_it(w[2])})', flush=True)
    if w[0] >= 0.0:
        CLKJ = (full, pool, xo)
        json.dump(full, open('scratch/work/au/journey_au9_CLK.json', 'w'))
        break

if CLKJ:
    full, pool, xo = CLKJ
    clk_items = U.journey_items('scratch/work/au/journey_au9_CLK.json',
                                'CAP_CLK')
    G2 = fields(pool, 'CAP_DATA', extra=clk_items)
    dat = astar(G2, (1, 69.90, 3.18), (0, 75.45, 22.845))
    print(f'DATA A* (XO ablated={xo}): {"FOUND" if dat else "NONE"}',
          flush=True)
    if dat:
        dat['net'] = 'CAP_DATA'
        print(f'   vias: {dat["vias"]}', flush=True)
        for r in dat['runs']:
            print(f'   L{r["layer"]}: {r["pts"][0]} -> {r["pts"][-1]} '
                  f'({len(r["pts"])} pts)', flush=True)
        json.dump(dat, open('scratch/work/au/journey_au9_DATA.json', 'w'))
        dat_items = journey_items_dense(dat, 'CAP_DATA')
        clk_items_d = journey_items_dense(full, 'CAP_CLK')
        w1 = check(clk_items_d, 'CAP_CLK', pool, dat_items)
        w2 = check(dat_items, 'CAP_DATA', pool, clk_items_d)
        print(f'PAIR exact: CLK worst {w1[0]:+.3f} '
              f'({L.fmt_it(w1[1])} vs {L.fmt_it(w1[2])})', flush=True)
        print(f'            DATA worst {w2[0]:+.3f} '
              f'({L.fmt_it(w2[1])} vs {L.fmt_it(w2[2])})', flush=True)
print('done', flush=True)
