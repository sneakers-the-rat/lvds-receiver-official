import sys, math
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')

def df(it, x, y):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = x - cx, y - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return math.hypot(max(abs(lx) - hw, 0.0), max(abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = x - x1, y - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else min(1, max(0, (px * dx + py * dy) / L2))
        return math.hypot(px - t * dx, py - t * dy) - hw
    return math.hypot(x - d[0], y - d[1]) - d[2]

for pt in ((73.5, 17.2), (73.4, 16.9), (73.6, 17.15), (72.6, 16.6)):
    vals = []
    for it in pool[2]:
        if it[1] == 'ULPI_STP':
            continue
        req = max(0.2, it[3])
        vals.append((df(it, *pt) - req, it))
    vals.sort(key=lambda v: v[0])
    print(f'point {pt}: worst B items:', flush=True)
    for v, it in vals[:4]:
        print(f'   G={v:+.3f}', L.fmt_it(it), flush=True)
