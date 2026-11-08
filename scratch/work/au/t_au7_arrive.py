"""t_au7: arrival + DATA re-plan in the TRUE build model.
Model: full exp241esc items minus PG corridor (55). CLK fixed =
B ride + In2 NE run from au2 journey, cut at via (64.75,16.95)
(the (69.5,22.35) via and F arrivals are re-planned).
Step 1: CLK arrival A* from (In2, 64.75,16.95) to (F, 75.45,25.385).
Step 2: DATA full A* from (In2, 69.9,3.18) to (F, 75.45,22.845)
with CLK's complete journey fenced as exact items (field rebuild).
Outputs journey JSONs for both."""
import sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
import t_au1_lib as U
import t_ai_lib as L
import pcbnew

PG_PRED = lambda l, it: l == 2 and it[1] == 'PG_3V3' \
    and 60 < U.item_centre(it)[0] < 70 and 0 < U.item_centre(it)[1] < 16

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items_full = L.load_items(board)
pool = {l: [it for it in items_full[l] if not PG_PRED(l, it)]
        for l in range(3)}


def astar(G, start, goal):
    """start/goal = (layer, x, y). Track legal G>=0.10, via minG>=0.25.
    Centering penalty as t_at30. Returns journey dict or None."""
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


def fields_with(extra):
    G = {}
    for l in range(3):
        lst = list(pool[l]) + extra.get(l, [])
        G[l], _, _ = U.build_field(lst, 'CAP_CLK')
    return G


# ---- CLK fixed head: au2 runs up to the (64.75,16.95) via
J = json.load(open('scratch/work/au/journey_au2_CAP_CLK_B_PG.json'))
head_runs = []
for run in J['runs']:
    head_runs.append(run)
    if run['pts'][-1] == [64.75, 16.95]:
        break
head = dict(vias=[[70.0, 1.8]], runs=head_runs)
print('CLK head runs:', [(r['layer'], r['pts'][0], r['pts'][-1])
                         for r in head_runs], flush=True)

G = fields_with({})
arr = astar(G, (1, 64.75, 16.95), (0, 75.45, 25.385))
print(f'CLK arrival A*: {"FOUND" if arr else "NONE"}', flush=True)
if arr:
    print(f'   arrival vias: {arr["vias"]}', flush=True)
    for r in arr['runs']:
        print(f'   L{r["layer"]}: {r["pts"][0]} -> {r["pts"][-1]}',
              flush=True)
    clk_full = dict(net='CAP_CLK',
                    vias=[[64.75, 16.95]] + arr['vias'],
                    runs=head_runs + arr['runs'])
    json.dump(clk_full, open('scratch/work/au/journey_au7_CLK.json', 'w'))
    # DATA A* with CLK fenced as items (decimated items are fine for
    # field building: field uses exact item geometry)
    clk_items = U.journey_items('scratch/work/au/journey_au7_CLK.json',
                                'CAP_CLK')
    G2 = {}
    for l in range(3):
        lst = list(pool[l]) + clk_items[l]
        G2[l], _, _ = U.build_field(lst, 'CAP_DATA')
    dat = astar(G2, (1, 69.90, 3.18), (0, 75.45, 22.845))
    print(f'DATA A*: {"FOUND" if dat else "NONE"}', flush=True)
    if dat:
        dat['net'] = 'CAP_DATA'
        print(f'   vias: {dat["vias"]}', flush=True)
        for r in dat['runs']:
            print(f'   L{r["layer"]}: {r["pts"][0]} -> {r["pts"][-1]} '
                  f'({len(r["pts"])} pts)', flush=True)
        json.dump(dat, open('scratch/work/au/journey_au7_DATA.json', 'w'))
print('done', flush=True)
