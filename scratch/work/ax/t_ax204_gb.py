import sys
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

for pt in ((70.15, 18.1), (70.4, 17.9), (69.9, 18.3), (70.6, 18.4)):
    vals = sorted(((df(it, *pt) - max(0.2, it[3]), it)
                   for it in pool[2] if it[1] != 'ULPI_STP'))
    print(f'B {pt}: G={vals[0][0]:+.3f}', L.fmt_it(vals[0][1]),
          '| 2nd', f"{vals[1][0]:+.3f}", L.fmt_it(vals[1][1]), flush=True)
