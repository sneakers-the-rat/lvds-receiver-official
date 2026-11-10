"""t_as34: fast group ablation. Sparse per-cell item contributions
(value<0.4) per layer; ablation = mask + np.minimum.at. Reachability via
labelled components + vectorized via-pair extraction. Prints progress."""
import wx
_app = wx.App(False)
import pcbnew, sys, math
import numpy as np
from scipy import ndimage
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass
from collections import deque

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)
X0, X1, Y0, Y1, ST = 63.0, 79.5, -3.0, 29.5, 0.05
xs = np.arange(X0, X1 + 1e-9, ST)
ys = np.arange(Y0, Y1 + 1e-9, ST)
GX, GY = np.meshgrid(xs, ys)
NY, NX = GX.shape
NCELL = NY * NX

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

GROUPS = [
    ('XO In2 web y17-22', lambda l, it: l == 1 and it[1] == 'XO'
        and 66 < item_centre(it)[0] < 76 and 16 < item_centre(it)[1] < 23),
    ('ULPI_NXT In2 diag', lambda l, it: l == 1 and it[1] == 'ULPI_NXT'
        and it[0] == 'seg' and abs(it[2][0] - 74.5) < 0.01),
    ('ULPI_DIR B diag', lambda l, it: l == 2 and it[1] == 'ULPI_DIR'
        and it[0] == 'seg' and abs(it[2][0] - 71.375) < 0.01),
    ('HV_SHDN In2 SW staircase', lambda l, it: l == 1 and it[1] == 'HV_SHDN'
        and item_centre(it)[0] < 70.2 and item_centre(it)[1] < 7),
    ('THR_DAC F+In2 W staircase', lambda l, it: it[1] == 'THR_DAC'
        and item_centre(it)[0] < 66),
    ('I2C_SCL In2 horizontal y12.5', lambda l, it: l == 1
        and it[1] == 'I2C_SCL' and it[0] == 'seg'
        and abs(it[2][1] - 12.5) < 0.2 and item_centre(it)[0] < 70),
    ('I2C_SCL In2 diagonal', lambda l, it: l == 1 and it[1] == 'I2C_SCL'
        and it[0] == 'seg' and item_centre(it)[1] < 8
        and item_centre(it)[0] < 70),
    ('+3V3D In2 horizontal y24.375', lambda l, it: l == 1
        and it[1] == '+3V3D' and it[0] == 'seg'
        and abs(it[2][1] - 24.375) < 0.01),
    ('CDR_LOL B jog', lambda l, it: l == 2 and it[1] == 'CDR_LOL'
        and item_centre(it)[1] < 4.5 and item_centre(it)[0] < 71),
    ('SPI_SCK In2 saddle', lambda l, it: l == 1 and it[1] == 'SPI_SCK'
        and 3.5 < item_centre(it)[1] < 6.5 and item_centre(it)[0] < 72.5),
    ('+3V3A via 69.125,4.375', lambda l, it: it[1] == '+3V3A'
        and it[0] == 'via' and abs(it[2][0] - 69.125) < 0.01),
    ('GND via 72.55,25.6', lambda l, it: it[1] == 'GND' and it[0] == 'via'
        and abs(it[2][0] - 72.55) < 0.01 and abs(it[2][1] - 25.6) < 0.01),
    ('XO via 71.625,25.625', lambda l, it: it[1] == 'XO' and it[0] == 'via'
        and abs(it[2][0] - 71.625) < 0.01),
    ('XO B vertical x72.625', lambda l, it: l == 2 and it[1] == 'XO'
        and it[0] == 'seg' and abs(it[2][0] - 72.625) < 0.01),
    ('CDR_DATN B set', lambda l, it: l == 2 and it[1] == 'CDR_DATN'
        and item_centre(it)[0] > 68),
    ('CDR_SQUELCH F wall', lambda l, it: l == 0 and it[1] == 'CDR_SQUELCH'
        and 70 < item_centre(it)[0] < 76 and 20 < item_centre(it)[1] < 28),
    ('+3V3D F web U5', lambda l, it: l == 0 and it[1] == '+3V3D'
        and 70 < item_centre(it)[0] < 76 and 20 < item_centre(it)[1] < 26),
    ('I2C_SDA via 69.9,0.82', lambda l, it: it[1] == 'I2C_SDA'
        and it[0] == 'via' and abs(it[2][1] - 0.82) < 0.01),
    ('BIST_DRV In2 jog+horizontal', lambda l, it: l == 1
        and it[1] == 'BIST_DRV' and item_centre(it)[1] > 10
        and item_centre(it)[0] < 70),
    ('ULPI_NXT via 62.625,12.75', lambda l, it: it[1] == 'ULPI_NXT'
        and it[0] == 'via' and abs(it[2][0] - 62.625) < 0.01),
    ('+3V3D via 74.625,24.375', lambda l, it: it[1] == '+3V3D'
        and it[0] == 'via' and abs(it[2][0] - 74.625) < 0.01),
    ('XO via 71.875,19.625', lambda l, it: it[1] == 'XO' and it[0] == 'via'
        and abs(it[2][0] - 71.875) < 0.01),
    ('ULPI_NXT via 74.5,19.25', lambda l, it: it[1] == 'ULPI_NXT'
        and it[0] == 'via' and abs(it[2][0] - 74.5) < 0.01),
]
GPRED = {name: pred for name, pred in GROUPS}

CASES = {
    'CAP_CLK':  dict(start=(70.02, 1.83), target=(75.45, 25.385)),
    'CAP_DATA': dict(start=(69.90, 3.18), target=(75.45, 22.845)),
}

for net, case in CASES.items():
    myclr = netclass(net)[1]
    # sparse contributions per layer
    sparse = {}
    group_of = {}  # (l, idx) -> set of group names containing it
    for l in range(3):
        cells, ids, vals = [], [], []
        for idx, it in enumerate(items[l]):
            if it[1] == net:
                continue
            for name, pred in GROUPS:
                if pred(l, it):
                    group_of.setdefault((l, idx), set()).add(name)
            bx0, bx1, by0, by1 = item_bbox(it)
            req = max(myclr, it[3])
            if bx1 < X0 - req - 0.3 or bx0 > X1 + req + 0.3 or \
               by1 < Y0 - req - 0.3 or by0 > Y1 + req + 0.3:
                continue
            f = (item_dist_field(it) - req).ravel()
            m = f < 0.4
            if m.any():
                ci = np.nonzero(m)[0]
                cells.append(ci)
                ids.append(np.full(ci.shape, idx, dtype=np.int32))
                vals.append(f[m])
        sparse[l] = (np.concatenate(cells), np.concatenate(ids),
                     np.concatenate(vals))
        print(f"{net} L{l}: {len(sparse[l][0])} sparse entries", flush=True)

    def build_G(abl_names):
        G = {}
        for l in range(3):
            cells, ids, vals = sparse[l]
            v = vals
            if abl_names:
                kill = np.array([any(nm in group_of.get((l, int(i)), ())
                                     for nm in abl_names) for i in ids]) \
                    if len(ids) else None
                v = np.where(kill, 9.9, vals)
            g = np.full(NCELL, 9.9, dtype=np.float64)
            np.minimum.at(g, cells, v)
            G[l] = g.reshape(NY, NX)
        return G

    def reachable(abl_names):
        G = build_G(abl_names)
        track = {l: G[l] >= 0.10 for l in range(3)}
        viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
        comp = {l: ndimage.label(track[l],
                                 structure=np.ones((3, 3)))[0]
                for l in range(3)}
        def cell(x, y):
            return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))
        sy, sx = cell(*case['start'])
        ty, tx = cell(*case['target'])
        if not track[0][ty, tx]:
            return False
        target_node = (0, int(comp[0][ty, tx]))
        adj = {}
        for a in range(3):
            for b in range(a + 1, 3):
                m = viafit & track[a] & track[b]
                if not m.any():
                    continue
                pairs = np.unique(np.stack([comp[a][m], comp[b][m]]),
                                  axis=1)
                for u, w in pairs.T:
                    adj.setdefault((a, int(u)), set()).add((b, int(w)))
                    adj.setdefault((b, int(w)), set()).add((a, int(u)))
        seen = set()
        dq = deque()
        for l in range(3):
            if track[l][sy, sx]:
                n = (l, int(comp[l][sy, sx]))
                seen.add(n)
                dq.append(n)
        while dq:
            n = dq.popleft()
            if n == target_node:
                return True
            for mm in adj.get(n, ()):
                if mm not in seen:
                    seen.add(mm)
                    dq.append(mm)
        return False

    print(f"== {net}: baseline = {reachable(())}", flush=True)
    openers = []
    for name, _ in GROUPS:
        r = reachable((name,))
        print(f"   '{name}': {r}", flush=True)
        if r:
            openers.append(name)
    print(f"== {net} single-group openers: {openers}", flush=True)
    if not openers:
        import itertools
        names = [n for n, _ in GROUPS]
        for a, b in itertools.combinations(names, 2):
            if reachable((a, b)):
                print(f"   PAIR OPENS: '{a}' + '{b}'", flush=True)
                openers.append((a, b))
                break
        print(f"== {net} openers after pair scan: {openers}", flush=True)
