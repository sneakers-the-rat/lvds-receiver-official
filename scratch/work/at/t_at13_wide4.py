"""t_at13: widest-path diagnosis on model v4 variants.
Variant A: SDA fanout via at (69.30,2.05) (near-pad, gate +0.050).
Variant B: SDA fanout via absent (diagnosis only).
Model v4 = esc + SCL In2 chord + band jog v4 (from V3) + S via
(70.05,0.82)+B re-lay + GND tree out + +3V3D web out + via shrink +
XO web out. Widest path per net per variant (sibling ignored)."""
import wx
_app = wx.App(False)
import pcbnew, sys, math, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

S = (70.05, 0.82)
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)

def key_seg(d):
    a = (round(d[0], 3), round(d[1], 3), round(d[2], 3), round(d[3], 3))
    b = (round(d[2], 3), round(d[3], 3), round(d[0], 3), round(d[1], 3))
    return a, b

BAND_JOG = [(68.875, 0.625, 69.125, 0.375), (69.125, 0.375, 69.375, 0.125),
            (69.375, 0.125, 69.625, -0.125),
            (69.625, -0.125, 69.875, -0.375),
            (69.875, -0.375, 70.125, -0.625)]
REM_SEGS = {
    1: [('HV_SHDN', s) for s in BAND_JOG] + [
        ('I2C_SCL', (67.875, 5.125, 68.875, 1.625)),
        ('I2C_SCL', (68.875, 1.625, 69.375, 1.375))],
    2: [('I2C_SDA', s) for s in [
        (69.900, 0.820, 69.875, 0.625), (69.875, 0.625, 69.875, -9.125)]],
    0: [('GND', s) for s in [
        (71.000, 0.270, 69.600, 0.250), (69.600, 0.250, 68.900, 0.850),
        (68.900, 0.850, 68.200, 1.150), (68.200, 1.150, 67.850, 1.220),
        (67.850, 1.220, 67.500, 0.950)]],
}
REM_VIAS = [(69.9, 0.82, 'I2C_SDA'), (69.32, 2.14, 'I2C_SDA')]

def build_pool(sda_via):
    pool = {0: [], 1: [], 2: []}
    for li in range(3):
        remkeys = set()
        for n, s in REM_SEGS.get(li, []):
            a, b = key_seg(s)
            remkeys.add((n, a)); remkeys.add((n, b))
        for it in items[li]:
            if it[0] == 'via':
                skip = False
                for vx, vy, vn in REM_VIAS:
                    if it[1] == vn and abs(it[2][0] - vx) < 0.01 and \
                       abs(it[2][1] - vy) < 0.01:
                        skip = True
                if skip:
                    continue
                if it[1] == '+3V3D' and abs(it[2][0] - 74.625) < 0.01 and \
                   abs(it[2][1] - 24.375) < 0.01:
                    pool[li].append(('via', '+3V3D', (74.625, 24.375, 0.25),
                                     it[3]))
                    continue
            if it[0] == 'seg':
                a, b = key_seg(it[2])
                if (it[1], a) in remkeys:
                    continue
                cx = (it[2][0] + it[2][2]) / 2
                cy = (it[2][1] + it[2][3]) / 2
                if li == 0 and it[1] == '+3V3D' and 70 < cx < 76 and \
                   20 < cy < 26:
                    continue
                if li == 1 and it[1] == 'XO' and 66 < cx < 76 and \
                   16 < cy < 23:
                    continue
            pool[li].append(it)
    def add_via(net, x, y, r=0.25):
        for li in range(3):
            pool[li].append(('via', net, (x, y, r), netclass(net)[1]))
    def add_seg(li, net, a, b, w):
        pool[li].append(('seg', net, (a[0], a[1], b[0], b[1], w / 2),
                         netclass(net)[1]))
    add_seg(1, 'I2C_SCL', (67.875, 5.125), (68.625, 2.5), 0.20)
    add_seg(1, 'I2C_SCL', (68.625, 2.5), (69.1, 1.6), 0.20)
    add_seg(1, 'I2C_SCL', (69.1, 1.6), (69.375, 1.375), 0.20)
    BANDV = [(68.625, 0.875), (68.75, 0.5), (69.0, 0.25), (69.25, 0.0),
             (69.5, -0.25), (69.75, -0.5), (70.125, -0.625)]
    for i in range(len(BANDV) - 1):
        add_seg(1, 'HV_SHDN', BANDV[i], BANDV[i + 1], 0.25)
    add_via('I2C_SDA', *S)
    add_seg(2, 'I2C_SDA', (69.875, -1.5), (69.875, -9.125), 0.25)
    add_seg(2, 'I2C_SDA', (69.875, -1.5), S, 0.25)
    if sda_via is not None:
        add_via('I2C_SDA', *sda_via)
    return pool

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

def build_fields(pool, net):
    myclr = netclass(net)[1]
    G, ARG = {}, {}
    for l in range(3):
        field = np.full(GX.shape, 9.9)
        arg = np.full(GX.shape, -1, dtype=int)
        cand = []
        for idx, it in enumerate(pool[l]):
            if it[1] == net:
                continue
            bx0, bx1, by0, by1 = item_bbox(it)
            req = max(myclr, it[3])
            if bx1 < X0 - req - 0.3 or bx0 > X1 + req + 0.3 or \
               by1 < Y0 - req - 0.3 or by0 > Y1 + req + 0.3:
                continue
            cand.append((idx, item_dist_field(it) - req))
        for idx, f in cand:
            m = f < field
            field = np.where(m, f, field)
            arg = np.where(m, idx, arg)
        G[l] = field
        ARG[l] = arg
    return G, ARG

def cell(x, y):
    return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))

CASES = {
    'CAP_CLK':  dict(start=(70.02, 1.83), target=(75.45, 25.385)),
    'CAP_DATA': dict(start=(69.90, 3.18), target=(75.45, 22.845)),
}

def widest(pool, net):
    G, ARG = build_fields(pool, net)
    case = CASES[net]
    viafit = np.minimum(np.minimum(G[0], G[1]), G[2])
    sc = cell(*case['start'])
    tc = cell(*case['target'])
    best = {}
    pq = [(-9.9, (1, sc[0], sc[1]))]
    best[(1, sc[0], sc[1])] = 9.9
    came = {}
    goal = None
    while pq:
        negb, p = heapq.heappop(pq)
        b = -negb
        if b < best.get(p, -9.9) - 1e-12:
            continue
        l, iy, ix = p
        if l == 0 and (iy, ix) == tc:
            goal = p
            break
        for l2 in range(3):
            if l2 == l:
                continue
            nb = min(b, float(viafit[iy, ix]) - 0.25)
            q = (l2, iy, ix)
            if nb > best.get(q, -9.9) + 1e-12:
                best[q] = nb
                came[q] = p
                heapq.heappush(pq, (-nb, q))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                jy, jx = iy + dy, ix + dx
                if not (0 <= jy < NY and 0 <= jx < NX):
                    continue
                nb = min(b, float(G[l][jy, jx]) - 0.10)
                q = (l, jy, jx)
                if nb > best.get(q, -9.9) + 1e-12:
                    best[q] = nb
                    came[q] = p
                    heapq.heappush(pq, (-nb, q))
    if goal is None:
        return None, None
    bval = best[goal]
    p = goal
    chain = [p]
    while p in came:
        p = came[p]
        chain.append(p)
    chain.reverse()
    binds = []
    for i, p in enumerate(chain):
        l, iy, ix = p
        v = float(G[l][iy, ix]) - 0.10
        if v <= bval + 0.01:
            ai = ARG[l][iy, ix]
            binds.append((l, round(float(xs[ix]), 2),
                          round(float(ys[iy]), 2), round(v, 3),
                          L.fmt_it(pool[l][ai]) if ai >= 0 else None))
        if i + 1 < len(chain) and chain[i + 1][0] != l:
            vv = float(viafit[iy, ix]) - 0.25
            if vv <= bval + 0.01:
                ai = ARG[l][iy, ix]
                binds.append((l, round(float(xs[ix]), 2),
                              round(float(ys[iy]), 2), round(vv, 3),
                              'VIAFIT ' + (L.fmt_it(pool[l][ai])
                                           if ai >= 0 else '?')))
    return bval, binds

for name, sv in (('A sdavia@(69.30,2.05)', (69.30, 2.05)),
                 ('B sdavia absent', None)):
    pool = build_pool(sv)
    for net in ('CAP_CLK', 'CAP_DATA'):
        b, binds = widest(pool, net)
        print(f'== [{name}] {net}: widest bottleneck = '
              f'{("None" if b is None else format(b, "+.3f"))}', flush=True)
        if binds:
            seen = set()
            n = 0
            for bd in binds:
                if bd[4] in seen:
                    continue
                seen.add(bd[4])
                n += 1
                if n > 14:
                    break
                print(f'   bind L{bd[0]} ({bd[1]},{bd[2]}) {bd[3]:+.3f} '
                      f'vs {bd[4]}', flush=True)
