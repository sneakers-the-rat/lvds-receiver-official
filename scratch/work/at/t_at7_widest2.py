"""t_at7: widest-path (maximin clearance) diagnosis for CAP nets in the
band-jog model (east jog: segs from (68.875,0.625) onward shifted by
(-d,-d); west 3 segs kept). Reports each net's widest-path bottleneck
value and the cell where it binds, alone (no sibling fencing).
Usage: t_at5_widest.py sx sy delta"""
import wx
_app = wx.App(False)
import pcbnew, sys, math, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

SX, SY, DELTA = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
S = (SX, SY)
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)

def key_seg(d):
    a = (round(d[0], 3), round(d[1], 3), round(d[2], 3), round(d[3], 3))
    b = (round(d[2], 3), round(d[3], 3), round(d[0], 3), round(d[1], 3))
    return a, b

BAND8 = [(68.375, 1.125, 68.625, 0.875),
         (68.625, 0.875, 68.875, 0.625), (68.875, 0.625, 69.125, 0.375),
         (69.125, 0.375, 69.375, 0.125), (69.375, 0.125, 69.625, -0.125),
         (69.625, -0.125, 69.875, -0.375), (69.875, -0.375, 70.125, -0.625)]
REM_SEGS = {
    1: [('HV_SHDN', s) for s in BAND8],
    2: [('I2C_SDA', s) for s in [
        (69.900, 0.820, 69.875, 0.625), (69.875, 0.625, 69.875, -9.125)]],
    0: [('GND', s) for s in [
        (71.000, 0.270, 69.600, 0.250), (69.600, 0.250, 68.900, 0.850),
        (68.900, 0.850, 68.200, 1.150), (68.200, 1.150, 67.850, 1.220),
        (67.850, 1.220, 67.500, 0.950)]],
}
pool = {0: [], 1: [], 2: []}
for li in range(3):
    remkeys = set()
    for n, s in REM_SEGS.get(li, []):
        a, b = key_seg(s)
        remkeys.add((n, a)); remkeys.add((n, b))
    for it in items[li]:
        if it[0] == 'via' and it[1] == 'I2C_SDA' and \
           abs(it[2][0] - 69.9) < 0.01 and abs(it[2][1] - 0.82) < 0.01:
            continue
        if it[0] == 'seg':
            a, b = key_seg(it[2])
            if (it[1], a) in remkeys:
                continue
            cx = (it[2][0] + it[2][2]) / 2
            cy = (it[2][1] + it[2][3]) / 2
            if li == 0 and it[1] == '+3V3D' and 70 < cx < 76 and 20 < cy < 26:
                continue
            if li == 1 and it[1] == 'XO' and 66 < cx < 76 and 16 < cy < 23:
                continue
        pool[li].append(it)

def add_via(net, x, y, r=0.25):
    for li in range(3):
        pool[li].append(('via', net, (x, y, r), netclass(net)[1]))

def add_seg(li, net, a, b, w):
    pool[li].append(('seg', net, (a[0], a[1], b[0], b[1], w / 2),
                     netclass(net)[1]))

d = DELTA / 2.0
# west 3 segs verbatim, transition, jogged east segs
add_seg(1, 'HV_SHDN', (68.125, 1.375), (68.375, 1.125), 0.25)
verts = [(68.375, 1.125), (68.875 - d, 0.625 - d), (69.125 - d, 0.375 - d),
         (69.375 - d, 0.125 - d), (69.625 - d, -0.125 - d),
         (69.875 - d, -0.375 - d), (70.125, -0.625)]
for i in range(len(verts) - 1):
    add_seg(1, 'HV_SHDN', verts[i], verts[i + 1], 0.25)
add_via('I2C_SDA', *S)
add_seg(2, 'I2C_SDA', (69.875, -1.5), (69.875, -9.125), 0.25)
add_seg(2, 'I2C_SDA', (69.875, -1.5), S, 0.25)

X0, X1, Y0, Y1, ST = 63.0, 79.5, -3.0, 29.5, 0.05
xs = np.arange(X0, X1 + 1e-9, ST)
ys = np.arange(Y0, Y1 + 1e-9, ST)
GX, GY = np.meshgrid(xs, ys)
NY, NX = GX.shape

def item_dist_field(it):
    kind, dd = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = dd
        dx, dy = GX - cx, GY - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = dd
        px, py = GX - x1, GY - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    cx, cy, r = dd
    return np.hypot(GX - cx, GY - cy) - r

def item_bbox(it):
    kind, dd = it[0], it[2]
    if kind == 'pad':
        r = math.hypot(dd[2], dd[3])
        return dd[0] - r, dd[0] + r, dd[1] - r, dd[1] + r
    if kind == 'seg':
        return (min(dd[0], dd[2]) - dd[4], max(dd[0], dd[2]) + dd[4],
                min(dd[1], dd[3]) - dd[4], max(dd[1], dd[3]) + dd[4])
    return dd[0] - dd[2], dd[0] + dd[2], dd[1] - dd[2], dd[1] + dd[2]

def build_fields(net):
    myclr = netclass(net)[1]
    G = {}
    for l in range(3):
        field = np.full(GX.shape, 9.9)
        for it in pool[l]:
            if it[1] == net:
                continue
            bx0, bx1, by0, by1 = item_bbox(it)
            req = max(myclr, it[3])
            if bx1 < X0 - req - 0.3 or bx0 > X1 + req + 0.3 or \
               by1 < Y0 - req - 0.3 or by0 > Y1 + req + 0.3:
                continue
            field = np.minimum(field, item_dist_field(it) - req)
        G[l] = field
    return G

def cell(x, y):
    return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))

CASES = {
    'CAP_CLK':  dict(start=(70.02, 1.83), target=(75.45, 25.385)),
    'CAP_DATA': dict(start=(69.90, 3.18), target=(75.45, 22.845)),
}

for net, case in CASES.items():
    G = build_fields(net)
    viafield = np.minimum(np.minimum(G[0], G[1]), G[2])
    sc = cell(*case['start'])
    tc = cell(*case['target'])
    # widest path: state (layer, iy, ix); value = bottleneck field so far.
    # Track cells use G[l] (need >=0.10), via transitions need viafield>=0.25.
    best = {}
    start = (1, sc[0], sc[1])
    best[start] = 9.9
    pq = [(-9.9, start)]
    came = {start: None}
    goalval = None
    while pq:
        negv, p = heapq.heappop(pq)
        v = -negv
        if v < best.get(p, -1) - 1e-9:
            continue
        l, iy, ix = p
        if l == 0 and (iy, ix) == tc:
            goalval = v
            goalp = p
            break
        for l2 in range(3):
            if l2 != l:
                nv = min(v, viafield[iy, ix] - 0.15)  # via needs +0.25 vs track 0.10: penalize 0.15
                q = (l2, iy, ix)
                if nv > best.get(q, -1) + 1e-9:
                    best[q] = nv
                    came[q] = p
                    heapq.heappush(pq, (-nv, q))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                jy, jx = iy + dy, ix + dx
                if not (0 <= jy < NY and 0 <= jx < NX):
                    continue
                nv = min(v, G[l][jy, jx])
                q = (l, jy, jx)
                if nv > best.get(q, -1) + 1e-9:
                    best[q] = nv
                    came[q] = p
                    heapq.heappush(pq, (-nv, q))
    if goalval is None:
        print(f'== {net}: no path at all', flush=True)
        continue
    # walk back, find the binding cell (min field along path)
    path = []
    p = goalp
    while p is not None:
        path.append(p)
        p = came[p]
    path.reverse()
    bind = None
    for p in path:
        l, iy, ix = p
        val = G[l][iy, ix]
        if bind is None or val < bind[0]:
            bind = (val, p)
    bv, bp = bind
    print(f'== {net}: widest bottleneck = {goalval:+.3f} '
          f'(need >= +0.100 track / +0.250 via); binds at L{bp[0]} '
          f'({xs[bp[2]]:.2f},{ys[bp[1]]:.2f}) field {bv:+.3f}', flush=True)
    # also print the worst 5 cells along the path
    cells = sorted(((G[p[0]][p[1], p[2]], p) for p in path))[:5]
    for val, p in cells:
        print(f'     L{p[0]} ({xs[p[2]]:.2f},{ys[p[1]]:.2f}) field {val:+.3f}',
              flush=True)
