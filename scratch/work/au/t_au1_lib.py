"""t_au1_lib: shared field/widest machinery for the au CAP pair work.
Grid + field conventions identical to t_at30/t_at31 (0.05 grid over
x[63,79.5] y[-3,29.5]; field = min over foreign items of dist - req;
track centre legal at field >= 0.10; via legal at min-field >= 0.25).
Fields are built with argmin + second-min tracking so single-item
ablations are exact without a rebuild."""
import wx
_app = wx.App(False)
import pcbnew, sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass, dist_to_item

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


def item_centre(it):
    d = it[2]
    if it[0] == 'seg':
        return ((d[0] + d[2]) / 2, (d[1] + d[3]) / 2)
    return (d[0], d[1])


def centre(it):
    return item_centre(it)


# UNION ablation (the v8 model both CAP singles are legal in)
ABL_PREDS = [
    lambda l, it: l == 1 and it[1] == 'HV_SHDN'
        and item_centre(it)[0] < 70.2 and item_centre(it)[1] < 7,
    lambda l, it: l == 1 and it[1] == 'XO'
        and 66 < item_centre(it)[0] < 76 and 16 < item_centre(it)[1] < 23,
    lambda l, it: l == 0 and it[1] == '+3V3D'
        and 70 < item_centre(it)[0] < 76 and 20 < item_centre(it)[1] < 26,
]


def load_pool(board_path='hw/pdlvds_rx.exp241esc.kicad_pcb', extra_abl=()):
    board = pcbnew.LoadBoard(board_path)
    items = L.load_items(board)
    pool = {0: [], 1: [], 2: []}
    for li in range(3):
        for it in items[li]:
            if any(p(li, it) for p in ABL_PREDS):
                continue
            if any(p(li, it) for p in extra_abl):
                continue
            pool[li].append(it)
    return pool


def journey_items(jfile, net):
    """Convert a journey JSON to exact items (decimated segs + vias)."""
    J = json.load(open(jfile))
    out = {0: [], 1: [], 2: []}
    for run in J['runs']:
        l = run['layer']
        pts = run['pts']
        keep = [pts[0]]
        for a, b, c in zip(pts, pts[1:], pts[2:]):
            v1 = (b[0] - a[0], b[1] - a[1])
            v2 = (c[0] - b[0], c[1] - b[1])
            if v1 != v2:
                keep.append(b)
        keep.append(pts[-1])
        # further decimate long straight runs to <=0.8mm chords
        dec = [keep[0]]
        for p in keep[1:]:
            if math.hypot(p[0] - dec[-1][0], p[1] - dec[-1][1]) > 0.8:
                dec.append(p)
            elif p is keep[-1]:
                dec.append(p)
        if dec[-1] != keep[-1]:
            dec.append(keep[-1])
        for a, b in zip(dec, dec[1:]):
            out[l].append(('seg', net, (a[0], a[1], b[0], b[1], 0.10), 0.2))
    for (vx, vy) in J['vias']:
        for l in range(3):
            out[l].append(('via', net, (vx, vy, 0.25), 0.2))
    return out


def build_field(items_l, net):
    """Return (field, argmin_idx, second_field) for one layer."""
    myclr = netclass(net)[1]
    f1 = np.full(GX.shape, 9.9)
    f2 = np.full(GX.shape, 9.9)
    am = np.full(GX.shape, -1, dtype=np.int32)
    for idx, it in enumerate(items_l):
        if it[1] == net:
            continue
        bx0, bx1, by0, by1 = item_bbox(it)
        req = max(myclr, it[3])
        if bx1 < X0 - req - 0.3 or bx0 > X1 + req + 0.3 or \
           by1 < Y0 - req - 0.3 or by0 > Y1 + req + 0.3:
            continue
        v = item_dist_field(it) - req
        better = v < f1
        f2 = np.where(better, f1, np.minimum(f2, v))
        f1 = np.where(better, v, f1)
        am = np.where(better, idx, am)
    return f1, am, f2


def build_fields(pool, net, extra=None):
    """extra: {layer: [items]} appended to pool copies (sibling journey)."""
    G, AM, F2 = {}, {}, {}
    for l in range(3):
        lst = list(pool[l])
        if extra:
            lst += extra.get(l, [])
        G[l], AM[l], F2[l] = build_field(lst, net)
    return G, AM, F2


def cell(x, y):
    return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))


CASES = {
    'CAP_CLK':  dict(start=(70.02, 1.83), target=(75.45, 25.385)),
    'CAP_DATA': dict(start=(69.90, 3.18), target=(75.45, 22.845)),
}


def widest(G, net):
    """Maximin path for net in field dict G. Returns (bottleneck, came,
    goal_state). Track value = G-0.10; via value = min G - 0.25."""
    case = CASES[net]
    sc = cell(*case['start'])
    tc = cell(*case['target'])
    INF = float('inf')

    def tval(l, iy, ix):
        return G[l][iy, ix] - 0.10

    def vval(iy, ix):
        return min(G[0][iy, ix], G[1][iy, ix], G[2][iy, ix]) - 0.25

    best = {}
    pq = []
    s0 = (1, sc[0], sc[1])
    v0 = tval(1, sc[0], sc[1])
    best[s0] = v0
    heapq.heappush(pq, (-v0, s0))
    came = {s0: None}
    goal = (0, tc[0], tc[1])
    while pq:
        negv, p = heapq.heappop(pq)
        v = -negv
        if v < best.get(p, -INF) - 1e-9:
            continue
        if p == goal:
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
                if 0 <= jy < NY and 0 <= jx < NX:
                    cand.append(((l, jy, jx), tval(l, jy, jx)))
        for q, w in cand:
            nv = min(v, w)
            if nv > best.get(q, -INF) + 1e-9:
                best[q] = nv
                came[q] = p
                heapq.heappush(pq, (-nv, q))
    return best.get(goal, -INF), came, goal


def widest_path_states(came, goal):
    path = []
    p = goal
    while p is not None:
        path.append(p)
        p = came.get(p)
    path.reverse()
    return path


def bind_items(G, AM, pool_with_extra, net, path, bval, tol=0.006):
    """Identify items binding at near-bottleneck states of the widest
    path. Returns list of (layer, item_index_in_layer_list, item,
    state_desc)."""
    out = []
    seen = set()
    states = widest_path_states(*path) if isinstance(path, tuple) else path
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
            if idx < 0:
                continue
            key = (l, idx)
            if key in seen:
                continue
            seen.add(key)
            it = pool_with_extra[l][idx]
            out.append((l, idx, it,
                        f'{kind} L{l} ({xs[ix]:.2f},{ys[iy]:.2f}) v={v:+.3f}'))
    return out
