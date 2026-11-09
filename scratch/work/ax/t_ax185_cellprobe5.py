import sys, math
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
arm = []
for it in pool[2]:
    if it[1] == 'PHY_1V8' and it[0] == 'seg' and it[2][1] >= 16.0 \
            and max(it[2][0], it[2][2]) <= 77.85:
        arm.append(it)
arm += [it for it in pool[2] if it[0] == 'via'
        and abs(it[2][0] - 71.375) < 0.01 and abs(it[2][1] - 17.625) < 0.01]
rip_items(arm)
fat = [it for it in pool[2] if it[1] == 'PHY_1V8' and it[0] == 'seg'
       and abs(it[2][4] - 0.3) < 1e-9 and it[2][1] < 15.5]
rip_items(fat)
add_items({2: [('seg', 'PHY_1V8',
                (it[2][0], it[2][1], it[2][2], it[2][3], 0.15), it[3])
               for it in fat]})

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

import itertools
for y in (11.2, 11.0, 10.8, 10.6, 10.4):
    row = f'y={y}: '
    for x in (76.05, 76.15, 76.25, 76.35, 76.45):
        vals = min((df(it, x, y) - max(0.2, it[3])
                    for it in pool[2] if it[1] != 'ULPI_STP'))
        row += f'{vals:+.2f} '
    print(row, flush=True)
print('x cols: 76.05 76.15 76.25 76.35 76.45', flush=True)

for pt in ((76.25, 11.0), (76.35, 10.8), (76.25, 10.8), (76.15, 11.0)):
    vals = sorted(((df(it, *pt) - max(0.2, it[3]), it)
                   for it in pool[2] if it[1] != 'ULPI_STP'))
    print(f'point {pt}:', flush=True)
    for v, it in vals[:3]:
        print(f'   G={v:+.3f}', L.fmt_it(it), flush=True)
