import sys, math
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
c20 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.5) < 0.01 and it[2][0] in (75.725, 77.275)]
rip_items(c20)
arm = []
for it in pool[2]:
    if it[1] == 'PHY_1V8' and it[0] == 'seg' and it[2][1] >= 16.0 \
            and max(it[2][0], it[2][2]) <= 77.85:
        arm.append(it)
for it in pool[0]:
    if it[1] == 'PHY_1V8' and it[0] == 'seg' and max(it[2][0], it[2][2]) < 72.0:
        arm.append(it)
arm += [it for it in pool[2] if it[0] == 'via'
        and ((abs(it[2][0] - 71.375) < 0.01 and abs(it[2][1] - 17.625) < 0.01)
             or (abs(it[2][0] - 73.434) < 0.01
                 and abs(it[2][1] - 17.685) < 0.01))]
rip_items(arm)
c22 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.0) < 0.01 and it[2][0] in (72.02, 72.98)]
rip_items(c22)

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

for pt in ((71.5, 17.4), (71.3, 17.6), (71.7, 17.5)):
    for l in range(3):
        vals = []
        for it in pool[l]:
            if it[1] == 'ULPI_STP':
                continue
            vals.append((df(it, *pt) - max(0.2, it[3]), it))
        vals.sort(key=lambda v: v[0])
        v, it = vals[0]
        print(f'point {pt} layer {l}: G={v:+.3f}', L.fmt_it(it), flush=True)
