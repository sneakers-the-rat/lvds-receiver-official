"""t_at31: t_at30 pair A* (strong centering); when the second net
fails, run the widest-path in the SAME field+sibling masks and
print the bottleneck cells' binding fences (deduped)."""
import wx
_app = wx.App(False)
import pcbnew, sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

src = open('scratch/work/at/t_at30_pair.py').read()
# cut t_at30 at the per-net loop; re-implement loop with diagnostics
head = src.split('sibling_block = {l:')[0]
exec(head)

from scipy import ndimage
sibling_block = {l: np.zeros((NY, NX), dtype=bool) for l in range(3)}
ORDER = __import__('os').environ.get('ORDER', 'CAP_CLK,CAP_DATA').split(',')

def run_astar(net, G):
    track = {l: (G[l] >= 0.10) & (~sibling_block[l]) for l in range(3)}
    viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
    for l in range(3):
        viafit &= ~sibling_block[l]
    case = CASES[net]
    sc = cell(*case['start'])
    tc = cell(*case['target'])
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
                if not (0 <= jy < NY and 0 <= jx < NX):
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
    return goal, came

def fence_at(net, l, x, y):
    box = (x - 2.2, x + 2.2, y - 2.2, y + 2.2)
    local = L.in_box_pool(pool_items, box, pad=0.6)
    mm, w = L.pt_margin(l, x, y, net, 0.10, local[l])
    return mm, w

# rebuild a pool dict like t_at26 for fence lookups (UNION ablation)
def centre(it):
    d = it[2]
    if it[0] == 'seg':
        return ((d[0] + d[2]) / 2, (d[1] + d[3]) / 2)
    return (d[0], d[1])
pool_items = {0: [], 1: [], 2: []}
for li in range(3):
    for it in items[li]:
        cx, cy = centre(it)
        if li == 1 and it[1] == 'HV_SHDN' and cx < 70.2 and cy < 7:
            continue
        if li == 1 and it[1] == 'XO' and 66 < cx < 76 and 16 < cy < 23:
            continue
        if li == 0 and it[1] == '+3V3D' and 70 < cx < 76 and 20 < cy < 26:
            continue
        pool_items[li].append(it)

for ni, net in enumerate(ORDER):
    if ni > 0:
        UNION = [p for k in ABL for p in ABL[k]]
    G = build_fields(net)
    goal, came = run_astar(net, G)
    print(f'== {net}: A* goal = {goal is not None}', flush=True)
    if goal is None:
        # widest with sibling masks
        case = CASES[net]
        sc = cell(*case['start'])
        tc = cell(*case['target'])
        INF = float('inf')
        def tval(l, iy, ix):
            if sibling_block[l][iy, ix]:
                return -INF
            return G[l][iy, ix] - 0.10
        def vval(iy, ix):
            if any(sibling_block[l][iy, ix] for l in range(3)):
                return -INF
            return min(G[0][iy, ix], G[1][iy, ix], G[2][iy, ix]) - 0.25
        best = {}
        pq = []
        s0 = (1, sc[0], sc[1])
        v0 = tval(1, sc[0], sc[1])
        best[s0] = v0
        heapq.heappush(pq, (-v0, s0))
        camew = {s0: None}
        while pq:
            negv, p = heapq.heappop(pq)
            v = -negv
            if v < best.get(p, -INF) - 1e-9:
                continue
            l, iy, ix = p
            if l == 0 and (iy, ix) == tc:
                break
            cand = []
            for l2 in range(3):
                if l2 != l:
                    cand.append(((l2, iy, ix), vval(iy, ix)))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    jy, jx = iy + dy, ix + dx
                    if 0 <= jy < NY and 0 <= jx < NX:
                        cand.append(((l, jy, jx), tval(l, jy, jx)))
            for q, w in cand:
                nv = min(v, w)
                if nv > best.get(q, -INF) + 1e-9:
                    best[q] = nv
                    camew[q] = p
                    heapq.heappush(pq, (-nv, q))
        gstate = (0, tc[0], tc[1])
        bval = best.get(gstate, -INF)
        print(f'   widest bottleneck = {bval:+.3f}', flush=True)
        path = []
        p = gstate
        while p is not None:
            path.append(p)
            p = camew.get(p)
        path.reverse()
        seen = set()
        for p, q in zip(path, path[1:]):
            if q[0] != p[0]:
                v = vval(p[1], p[2])
                kind = 'viafit'
                cellq = p
            else:
                v = tval(q[0], q[1], q[2])
                kind = 'track'
                cellq = q
            if v <= bval + 0.004:
                l, iy, ix = cellq
                x, y = float(xs[ix]), float(ys[iy])
                mm, w = fence_at(net, l, x, y)
                key = L.fmt_it(w) if w else 'SIBLING-BLOCK'
                if sibling_block[l][iy, ix]:
                    key = 'SIBLING-BLOCK'
                if key in seen:
                    continue
                seen.add(key)
                print(f'   bind L{l} ({x:.2f},{y:.2f}) {kind} '
                      f'{v:+.3f} vs {key}', flush=True)
        continue
    # success: fence the sibling
    path = []
    p = goal
    while p is not None:
        path.append(p)
        p = came[p]
    path.reverse()
    runs = []
    vias = []
    cur = [path[0]]
    for p in path[1:]:
        if p[0] == cur[-1][0]:
            cur.append(p)
        else:
            runs.append(cur)
            vias.append((float(xs[cur[-1][2]]), float(ys[cur[-1][1]])))
            cur = [p]
    runs.append(cur)
    print(f'   vias: {vias}', flush=True)
    # add journey to pool_items as fences for diagnostics parity
    for run in runs:
        l = run[0][0]
        pts = [(float(xs[p[2]]), float(ys[p[1]])) for p in run]
        for a, b in zip(pts, pts[1:]):
            pool_items[l].append(('seg', net, (a[0], a[1], b[0], b[1],
                                               0.10), 0.2))
        m = np.zeros((NY, NX), dtype=bool)
        for (_, iy, ix) in run:
            m[iy, ix] = True
        sibling_block[l] |= ndimage.binary_dilation(
            m, structure=np.ones((17, 17)))
    for (vx, vy) in vias:
        for li in range(3):
            pool_items[li].append(('via', net, (vx, vy, 0.25), 0.2))
        vyi, vxi = cell(vx, vy)
        for l in range(3):
            sub = np.zeros((NY, NX), dtype=bool)
            sub[vyi, vxi] = True
            sibling_block[l] |= ndimage.binary_dilation(
                sub, structure=np.ones((29, 29)))
