"""t_as33: group ablation on the flood fields. For each candidate fence
GROUP (a net's item set in a box, one layer or all), recompute G without
those items and test BFS reachability start->target for both CAP nets.
A group whose removal opens a net is a re-lay candidate."""
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

CASES = {
    'CAP_CLK':  dict(start=(70.02, 1.83), target=(75.45, 25.385)),
    'CAP_DATA': dict(start=(69.90, 3.18), target=(75.45, 22.845)),
}
# group: (name, predicate(layer, item) -> bool)
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
]

def reachable(net, case, skip):
    myclr = netclass(net)[1]
    G = {}
    for l in range(3):
        field = np.full(GX.shape, 9.9)
        for it in items[l]:
            if it[1] == net or skip(l, it):
                continue
            bx0, bx1, by0, by1 = item_bbox(it)
            req = max(myclr, it[3])
            if bx1 < X0 - req - 0.3 or bx0 > X1 + req + 0.3 or \
               by1 < Y0 - req - 0.3 or by0 > Y1 + req + 0.3:
                continue
            field = np.minimum(field, item_dist_field(it) - req)
        G[l] = field
    track = {l: G[l] >= 0.10 for l in range(3)}
    viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25
    comp = {}
    for l in range(3):
        comp[l] = ndimage.label(track[l], structure=np.ones((3, 3)))[0]
    def cell(x, y):
        return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))
    sy, sx = cell(*case['start'])
    ty, tx = cell(*case['target'])
    if not track[0][ty, tx]:
        return False
    target_node = (0, comp[0][ty, tx])
    adj = {}
    for (cy, cx) in np.argwhere(viafit):
        ls = [l for l in range(3) if track[l][cy, cx]]
        for i in range(len(ls)):
            for j in range(i + 1, len(ls)):
                a = (ls[i], comp[ls[i]][cy, cx])
                b = (ls[j], comp[ls[j]][cy, cx])
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)
    seen = set()
    dq = deque()
    for l in range(3):
        if track[l][sy, sx]:
            n = (l, comp[l][sy, sx])
            seen.add(n)
            dq.append(n)
    while dq:
        n = dq.popleft()
        if n == target_node:
            return True
        for m in adj.get(n, ()):
            if m not in seen:
                seen.add(m)
                dq.append(m)
    return False

noskip = lambda l, it: False
for net, case in CASES.items():
    base = reachable(net, case, noskip)
    print(f"== {net}: baseline reachable = {base}")
    for name, pred in GROUPS:
        n_items = sum(1 for l in range(3) for it in items[l] if pred(l, it))
        r = reachable(net, case, pred)
        print(f"   group '{name}' ({n_items} items): reachable = {r}")
