"""t_au8: widest-path diagnosis of the CLK arrival segment
(In2 64.75,16.95 -> F 75.45,25.385) in the full-minus-PG model;
then with the +3V3D F web in the U5 box ablated, re-run widest + A*."""
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


def widest_from(G, start, goal, net):
    sc = U.cell(start[1], start[2])
    tc = U.cell(goal[1], goal[2])
    INF = float('inf')

    def tval(l, iy, ix):
        return G[l][iy, ix] - 0.10

    def vval(iy, ix):
        return min(G[0][iy, ix], G[1][iy, ix], G[2][iy, ix]) - 0.25
    best = {}
    pq = []
    s0 = (start[0], sc[0], sc[1])
    v0 = tval(start[0], sc[0], sc[1])
    best[s0] = v0
    heapq.heappush(pq, (-v0, s0))
    came = {s0: None}
    gst = (goal[0], tc[0], tc[1])
    while pq:
        negv, p = heapq.heappop(pq)
        v = -negv
        if v < best.get(p, -INF) - 1e-9:
            continue
        if p == gst:
            break
        l, iy, ix = p
        cand = []
        for l2 in range(3):
            if l2 != l:
                cand.append(((l2, iy, ix), vval(iy, ix)))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                jy, jx = iy + dy, ix + dx
                if 0 <= jy < U.NY and 0 <= jx < U.NX:
                    cand.append(((l, jy, jx), tval(l, jy, jx)))
        for q, w in cand:
            nv = min(v, w)
            if nv > best.get(q, -INF) + 1e-9:
                best[q] = nv
                came[q] = p
                heapq.heappush(pq, (-nv, q))
    return best.get(gst, -INF), came, gst


def binds(G, AM, comb, came, gst, bval, net, tol=0.006):
    states = []
    p = gst
    while p is not None:
        states.append(p)
        p = came.get(p)
    states.reverse()
    seen = set()
    out = []
    for p, q in zip(states, states[1:]):
        if q[0] != p[0]:
            v = min(G[0][p[1], p[2]], G[1][p[1], p[2]],
                    G[2][p[1], p[2]]) - 0.25
            cells = [(l, p[1], p[2]) for l in range(3)]
            kind = 'via'
        else:
            v = G[q[0]][q[1], q[2]] - 0.10
            cells = [q]
            kind = 'track'
        if v > bval + tol:
            continue
        for (l, iy, ix) in cells:
            if kind == 'track' and l != q[0]:
                continue
            idx = AM[l][iy, ix]
            if idx < 0 or (l, idx) in seen:
                continue
            seen.add((l, idx))
            out.append((l, comb[l][idx],
                        f'{kind} L{l} ({U.xs[ix]:.2f},{U.ys[iy]:.2f}) '
                        f'v={v:+.3f}'))
    return out


START = (1, 64.75, 16.95)
GOAL = (0, 75.45, 25.385)

for label, extra_pred in [
        ('FULL', lambda l, it: False),
        ('NO_+3V3D_F_U5', lambda l, it: l == 0 and it[1] == '+3V3D'
         and it[0] in ('seg','via') and 68 < U.item_centre(it)[0] < 77 and 19 < U.item_centre(it)[1] < 27),
        ('NO_+3V3D_F_U5+XO_In2', lambda l, it:
         (l == 0 and it[1] == '+3V3D' and 68 < U.item_centre(it)[0] < 77
          and 19 < U.item_centre(it)[1] < 27)
         or (l == 1 and it[1] == 'XO' and 66 < U.item_centre(it)[0] < 76
             and 16 < U.item_centre(it)[1] < 23))]:
    pool = {l: [it for it in items_full[l]
                if not PG_PRED(l, it) and not extra_pred(l, it)]
            for l in range(3)}
    G, AM = {}, {}
    for l in range(3):
        G[l], AM[l], _ = U.build_field(pool[l], 'CAP_CLK')
    bv, came, gst = widest_from(G, START, GOAL, 'CAP_CLK')
    print(f'== {label}: arrival widest {bv:+.3f}', flush=True)
    if label == 'FULL':
        for (l, it, desc) in binds(G, AM, pool, came, gst, bv, 'CAP_CLK'):
            print(f'   bind L{l} {L.fmt_it(it)} @ {desc}', flush=True)
print('done', flush=True)
