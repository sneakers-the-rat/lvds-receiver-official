"""t_as40: ASCII map of In2 passability, SW box, t_as39 CLK model."""
import wx
_app = wx.App(False)
import pcbnew, sys, math
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

RIP_SEGS = {
    (67.375, 2.125, 67.125, 2.375), (67.125, 2.375, 66.875, 2.625),
    (66.875, 2.625, 66.625, 2.875), (66.625, 2.875, 66.375, 3.125),
    (66.375, 3.125, 66.125, 3.375), (66.125, 3.375, 65.875, 3.625),
    (65.875, 3.625, 65.625, 3.875),
}
def is_rip(l, it):
    if l != 1 or it[1] != 'HV_SHDN' or it[0] != 'seg':
        return False
    d = it[2]
    key = (round(d[0], 3), round(d[1], 3), round(d[2], 3), round(d[3], 3))
    return key in RIP_SEGS or (key[2], key[3], key[0], key[1]) in RIP_SEGS

HOP = [('via', 'HV_SHDN', (67.6, 1.95, 0.25), 0.2),
       ('via', 'HV_SHDN', (65.4, 4.15, 0.25), 0.2),
       ('seg', 'HV_SHDN', (67.375, 2.125, 67.6, 1.95, 0.125), 0.2),
       ('seg', 'HV_SHDN', (65.4, 4.15, 65.625, 3.875, 0.125), 0.2)]

def dist_field(it):
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

def cell(x, y):
    return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))

net = 'CAP_CLK'
myclr = netclass(net)[1]
l = 1
field = np.full(GX.shape, 9.9)
pool = [it for it in items[l] if it[1] != net and not is_rip(l, it)] + HOP
for it in pool:
    bx0, bx1, by0, by1 = item_bbox(it)
    req = max(myclr, it[3])
    if bx1 < X0 - req - 0.3 or bx0 > X1 + req + 0.3 or \
       by1 < Y0 - req - 0.3 or by0 > Y1 + req + 0.3:
        continue
    field = np.minimum(field, dist_field(it) - req)
track = field >= 0.10
for iy in range(cell(0, 10.0)[0], cell(0, -1.0)[0] - 1, -2):
    row = []
    for ix in range(cell(62.5, 0)[1], cell(71.5, 0)[1] + 1, 2):
        x, y = xs[ix], ys[iy]
        if abs(x - 70.02) < 0.08 and abs(y - 1.83) < 0.08:
            row.append('S')
        elif abs(x - 69.9) < 0.08 and abs(y - 3.18) < 0.08:
            row.append('D')
        else:
            row.append('.' if track[iy, ix] else '#')
    print(f"y={ys[iy]:6.2f} " + ''.join(row))
print("x 62.5..71.5 step 0.1; S=CLK via D=DATA via (In2, t_as39 CLK model)")
