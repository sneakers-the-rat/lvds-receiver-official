#!/usr/bin/env python3
"""Exact-model waypoint (visibility) router.
Nodes: ring/offset points around every fence item + coarse grid; edges gated
by seg_margin (the exact gate). Layer changes at via-feasible nodes.
Usage: t_aq28_vgraph.py BOARD NET SX SY SL GX GY GL X0 X1 Y0 Y1 [EXTRA_JSON]
SL/GL: layer index 0/1/2, or 3 = via point (all layers).
Env: RINGR (candidate ring radius pad, default extra 0.02), GRID (coarse, 0.5),
K (neighbours, 14), THR (gate threshold, -0.001).
Prints one JSON plan line like t_aq26_router."""
import sys, os, json, math, heapq
import wx
_app = wx.App(False)
sys.path.insert(0, 'scratch/work/ai')
import pcbnew
import t_ai_lib as L

board = pcbnew.LoadBoard(sys.argv[1])
NET = sys.argv[2]
SX, SY, SL = float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
GX, GY, GL = float(sys.argv[6]), float(sys.argv[7]), int(sys.argv[8])
X0, X1, Y0, Y1 = (float(v) for v in sys.argv[9:13])
EXTRA = json.loads(sys.argv[13]) if len(sys.argv) > 13 else []
THR = float(os.environ.get('THR', '-0.001'))
K = int(os.environ.get('K', '14'))
GRID = float(os.environ.get('GRID', '0.5'))
RPAD = float(os.environ.get('RPAD', '0.005'))

items = L.load_items(board)
for e in EXTRA:
    net, li, ax, ay, bx, by, w = e
    items[li].append(('seg', net, (ax, ay, bx, by, w / 2), None))
box = (X0 - 1.2, X1 + 1.2, Y0 - 1.2, Y1 + 1.2)
pools = {}
for li in range(3):
    pools[li] = [it for it in items[li] if it[1] != NET]

def pt_ok(li, x, y, rad):
    return L.pt_margin(li, x, y, NET, rad, pools[li])[0] >= THR

def seg_ok(li, a, b):
    return L.seg_margin(li, a, b, NET, 0.1, pools[li], step=0.04)[0] >= THR

# ---- candidate points (x, y) independent of layer; layer fit tested per node
cand = set()
def addp(x, y):
    if X0 - 0.6 <= x <= X1 + 0.6 and Y0 - 0.6 <= y <= Y1 + 0.6:
        cand.add((round(x, 3), round(y, 3)))
for li in range(3):
    for it in pools[li]:
        kind = it[0]
        if kind == 'via':
            _, _n, (x, y, r), _ = it
            if not (X0 - 1.2 < x < X1 + 1.2 and Y0 - 1.2 < y < Y1 + 1.2): continue
            rr = r + 0.1 + L.pair_clr(NET, _n) + RPAD
            for k in range(12):
                a = k * math.pi / 6
                addp(x + rr * math.cos(a), y + rr * math.sin(a))
        elif kind == 'seg':
            _, _, (ax, ay, bx, by, hw), _ = it
            mx, my = (ax + bx) / 2, (ay + by) / 2
            if not (X0 - 1.2 < mx < X1 + 1.2 and Y0 - 1.2 < my < Y1 + 1.2): continue
            d = math.hypot(bx - ax, by - ay) or 1.0
            nx, ny = -(by - ay) / d, (bx - ax) / d
            off = hw + 0.1 + L.pair_clr(NET, it[1]) + RPAD
            for t in (0.0, 0.25, 0.5, 0.75, 1.0):
                px, py = ax + (bx - ax) * t, ay + (by - ay) * t
                addp(px + nx * off, py + ny * off)
                addp(px - nx * off, py - ny * off)
            for (px, py) in ((ax, ay), (bx, by)):
                rr = hw + 0.1 + L.pair_clr(NET, it[1]) + RPAD
                for k in range(8):
                    a = k * math.pi / 4
                    addp(px + rr * math.cos(a), py + rr * math.sin(a))
        elif kind == 'pad':
            _, _, (x, y, hwx, hwy, rot), _ = it
            if not (X0 - 1.2 < x < X1 + 1.2 and Y0 - 1.2 < y < Y1 + 1.2): continue
            off = 0.1 + L.pair_clr(NET, it[1]) + RPAD
            for sx in (-1, 0, 1):
                for sy in (-1, 0, 1):
                    if sx == 0 and sy == 0: continue
                    addp(x + sx * (hwx + off), y + sy * (hwy + off))
gx = X0
while gx <= X1:
    gy = Y0
    while gy <= Y1:
        addp(gx, gy); gy += GRID
    gx += GRID

nodes = []          # (x, y, li)
nidx = {}
for (x, y) in cand:
    for li in range(3):
        if pt_ok(li, x, y, 0.1):
            nidx[(x, y, li)] = len(nodes); nodes.append((x, y, li))
# via-feasible points (for layer change): point fits d0.5 via on all layers
via_pts = set()
for (x, y) in cand:
    if all(pt_ok(li, x, y, 0.25) for li in range(3)):
        via_pts.add((x, y))
print(f'// nodes {len(nodes)} cand {len(cand)} via_pts {len(via_pts)}', file=sys.stderr)

def add_special(x, y, layers):
    ids = []
    for li in layers:
        key = (round(x, 3), round(y, 3), li)
        if key not in nidx:
            nidx[key] = len(nodes); nodes.append((x, y, li))
        ids.append(nidx[key])
    return ids
SLs = range(3) if SL == 3 else [SL]
GLs = range(3) if GL == 3 else [GL]
starts = add_special(SX, SY, SLs)
goals = set(add_special(GX, GY, GLs))
if (round(SX, 3), round(SY, 3)) not in via_pts and SL == 3:
    via_pts.add((round(SX, 3), round(SY, 3)))
if (round(GX, 3), round(GY, 3)) not in via_pts and GL == 3:
    via_pts.add((round(GX, 3), round(GY, 3)))

# neighbours per layer by coarse bucketing
from collections import defaultdict
buckets = defaultdict(list)
for i, (x, y, li) in enumerate(nodes):
    buckets[(li, int(x // 2.0), int(y // 2.0))].append(i)
def neighbours(i):
    x, y, li = nodes[i]
    bx, by = int(x // 2.0), int(y // 2.0)
    pool = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            pool += buckets.get((li, bx + dx, by + dy), [])
    pool.sort(key=lambda j: (nodes[j][0] - x) ** 2 + (nodes[j][1] - y) ** 2)
    return pool[:K + 6]

INF = float('inf')
dist = {s: 0.0 for s in starts}
prev = {}
pq = [(0.0, s) for s in starts]
heapq.heapify(pq)
goal_hit = None
while pq:
    d, i = heapq.heappop(pq)
    if d > dist.get(i, INF): continue
    if i in goals:
        goal_hit = i; break
    x, y, li = nodes[i]
    # same-layer edges
    for j in neighbours(i):
        if j == i: continue
        x2, y2, _ = nodes[j]
        dd = math.hypot(x2 - x, y2 - y)
        if dd < 0.05 or dd > 3.2: continue
        if seg_ok(li, (x, y), (x2, y2)):
            nd = d + dd
            if nd < dist.get(j, INF):
                dist[j] = nd; prev[j] = (i, 'seg'); heapq.heappush(pq, (nd, j))
    # layer change
    if (x, y) in via_pts:
        for lj in range(3):
            if lj == li: continue
            j = nidx.get((x, y, lj))
            if j is None: continue
            nd = d + 4.0
            if nd < dist.get(j, INF):
                dist[j] = nd; prev[j] = (i, 'via'); heapq.heappush(pq, (nd, j))
assert goal_hit is not None, 'NO PATH (vgraph)'
chain = []
i = goal_hit
while i not in starts:
    p, kind = prev[i]
    chain.append((kind, nodes[i], nodes[p]))
    i = p
chain.reverse()
plan = []
for kind, (x2, y2, li2), (x1, y1, li1) in chain:
    if kind == 'via':
        plan.append(['via', NET, x1, y1])
    else:
        plan.append(['seg', NET, li1, x1, y1, x2, y2, 0.2])
print(f'// plan items {len(plan)} cost {dist[goal_hit]:.1f}', file=sys.stderr)
print(json.dumps(plan))
