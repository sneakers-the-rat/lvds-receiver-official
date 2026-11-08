"""t_as31: bottleneck (minimax-deficit) path for the CAP nets in the exact
item model + ablation test of the items blocking the waist.
Track cell deficit on layer l: max(0, 0.10 - G_l). Via deficit at a cell:
max(0, 0.25 - min_l G_l). Path cost = max deficit along it (Dijkstra).
Top-3 minima per cell/layer retained so single/double item ablation is a
field lookup, not a recompute."""
import wx
_app = wx.App(False)
import pcbnew, sys, math, heapq, itertools
import numpy as np
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)

X0, X1, Y0, Y1, ST = 63.0, 79.5, -3.0, 29.5, 0.05
xs = np.arange(X0, X1 + 1e-9, ST)
ys = np.arange(Y0, Y1 + 1e-9, ST)
GX, GY = np.meshgrid(xs, ys)
NY, NX = GX.shape

def item_dist_field(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = GX - cx, GY - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = GX - x1, GY - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    cx, cy, r = d
    return np.hypot(GX - cx, GY - cy) - r

def item_bbox(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        r = math.hypot(d[2], d[3])
        return d[0] - r, d[0] + r, d[1] - r, d[1] + r
    if kind == 'seg':
        return (min(d[0], d[2]) - d[4], max(d[0], d[2]) + d[4],
                min(d[1], d[3]) - d[4], max(d[1], d[3]) + d[4])
    return d[0] - d[2], d[0] + d[2], d[1] - d[2], d[1] + d[2]

CASES = {
    'CAP_CLK':  dict(start=(70.02, 1.83), target=(75.45, 25.385)),
    'CAP_DATA': dict(start=(69.90, 3.18), target=(75.45, 22.845)),
}
CAP = 0.65  # cells with deficit above this are walls for the search

for net, case in CASES.items():
    myclr = netclass(net)[1]
    # top-3 fields per layer: values V[l][k], item ids I[l][k]
    V = {l: np.full((3, NY, NX), 9.9) for l in range(3)}
    I = {l: np.full((3, NY, NX), -1, dtype=np.int32) for l in range(3)}
    flat_items = {}
    for l in range(3):
        lst = []
        for idx, it in enumerate(items[l]):
            if it[1] == net:
                continue
            bx0, bx1, by0, by1 = item_bbox(it)
            req = max(myclr, it[3])
            if bx1 < X0 - req - 0.3 or bx0 > X1 + req + 0.3 or \
               by1 < Y0 - req - 0.3 or by0 > Y1 + req + 0.3:
                continue
            lst.append((idx, it, item_dist_field(it) - req))
        flat_items[l] = {idx: it for idx, it, _ in lst}
        for idx, it, f in lst:
            v = V[l]; ii = I[l]
            better = f < v[0]
            v[2] = np.where(better & (v[1] < v[2]), v[1], v[2])
            ii[2] = np.where(better & (v[1] < v[2]), ii[1], ii[2])
            v[1] = np.where(better & (v[0] < v[1]), v[0], v[1])
            ii[1] = np.where(better & (v[0] < v[1]), ii[0], ii[1])
            v[0] = np.where(better, f, v[0])
            ii[0] = np.where(better, idx, ii[0])
            # also insert into slots 1,2 when not better than slot0
            ins = (~better)
            b1 = ins & (f < v[1])
            v[2] = np.where(b1 & (v[1] < v[2]), v[1], v[2])
            ii[2] = np.where(b1 & (v[1] < v[2]), ii[1], ii[2])
            v[1] = np.where(b1, f, v[1])
            ii[1] = np.where(b1, idx, ii[1])
            b2 = ins & (~b1) & (f < v[2])
            v[2] = np.where(b2, f, v[2])
            ii[2] = np.where(b2, idx, ii[2])
    def G(l, abl=frozenset()):
        v = V[l].copy(); ii = I[l]
        for k in range(3):
            m = np.isin(ii[k], list(abl)) if abl else None
            if abl:
                v[k] = np.where(m, 9.9, v[k])
        return v.min(axis=0)
    def cell(x, y):
        return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))
    sy, sx = cell(*case['start'])
    ty, tx = cell(*case['target'])

    def bottleneck(abl=frozenset()):
        g = {l: G(l, abl) for l in range(3)}
        gmin = np.minimum(np.minimum(g[0], g[1]), g[2])
        tdef = {l: np.maximum(0.0, 0.10 - g[l]) for l in range(3)}
        vdef = np.maximum(0.0, 0.25 - gmin)
        dist = np.full((3, NY, NX), 1e9)
        par = {}
        pq = []
        for l in range(3):
            dist[l, sy, sx] = 0.0
            heapq.heappush(pq, (0.0, l, sy, sx))
        goal = None
        while pq:
            c, l, iy, ix = heapq.heappop(pq)
            if c > dist[l, iy, ix] + 1e-12:
                continue
            if l == 0 and iy == ty and ix == tx:
                goal = (l, iy, ix)
                break
            for dl in (-1, 1):
                l2 = l + dl
                if 0 <= l2 < 3:
                    nc = max(c, float(vdef[iy, ix]))
                    if nc <= CAP and nc < dist[l2, iy, ix] - 1e-12:
                        dist[l2, iy, ix] = nc
                        par[(l2, iy, ix)] = (l, iy, ix)
                        heapq.heappush(pq, (nc, l2, iy, ix))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    jy, jx = iy + dy, ix + dx
                    if 0 <= jy < NY and 0 <= jx < NX:
                        nc = max(c, float(tdef[l][jy, jx]))
                        if nc <= CAP and nc < dist[l, jy, jx] - 1e-12:
                            dist[l, jy, jx] = nc
                            par[(l, jy, jx)] = (l, iy, ix)
                            heapq.heappush(pq, (nc, l, jy, jx))
        if goal is None:
            return None, None, g
        # walk back
        path = []
        node = goal
        while node in par:
            path.append(node)
            node = par[node]
        path.append((0, sy, sx) if False else node)
        path.reverse()
        return dist[goal], path, g

    b, path, g = bottleneck()
    print(f"== {net}: bottleneck deficit = {b if b is None else round(b,3)}")
    if path:
        waist = {}
        seq = []
        for (l, iy, ix) in path:
            d = max(0.0, 0.10 - g[l][iy, ix])
            if d > 0.01:
                iid = I[l][0, iy, ix]
                it = flat_items[l].get(int(iid))
                key = (l, int(iid))
                waist[key] = waist.get(key, 0) + 1
                if it:
                    seq.append((round(float(xs[ix]), 2), round(float(ys[iy]), 2),
                                l, round(d, 3), it[1], it[0], it[2]))
        print("   waist cells (deficit>0.01):", len(seq))
        for s_ in seq[::max(1, len(seq) // 25)]:
            print("     ", s_)
        print("   responsible items (layer, item) -> waist cells:")
        cand = []
        for (l, iid), n in sorted(waist.items(), key=lambda kv: -kv[1]):
            it = flat_items[l].get(iid)
            if it:
                print(f"     L{l} {it[1]} {it[0]} {it[2]}  cells={n}")
                cand.append((l, iid))
        # ablation: singles then pairs among top candidates
        def reachable(abl):
            bb, _, _ = bottleneck(abl)
            return bb is not None and bb <= 0.001
        done = False
        for (l, iid) in cand[:6]:
            if reachable(frozenset({(l, iid)})):
                it = flat_items[l][iid]
                print(f"   ABLATION OPENS: single L{l} {it[1]} {it[0]} {it[2]}")
                done = True
        if not done:
            for a, bb_ in itertools.combinations(cand[:5], 2):
                if reachable(frozenset({a, bb_})):
                    ia, ib = flat_items[a[0]][a[1]], flat_items[bb_[0]][bb_[1]]
                    print(f"   ABLATION OPENS: pair L{a[0]} {ia[1]} {ia[0]} {ia[2]}"
                          f" + L{bb_[0]} {ib[1]} {ib[0]} {ib[2]}")
                    done = True
                    break
        if not done:
            print("   no single/pair ablation among top candidates opens it")
