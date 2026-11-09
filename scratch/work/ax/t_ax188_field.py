import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
c20 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.5) < 0.01 and it[2][0] in (75.725, 77.275)]
rip_items(c20)
add_items({0: [('pad', 'XI', (75.72, 18.75, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (76.68, 18.75, 0.280, 0.310, 0.0), 0.2)]})
c22 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.0) < 0.01 and it[2][0] in (72.02, 72.98)]
rip_items(c22)
add_items({0: [('pad', 'PHY_1V8', (79.12, 18.6, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (80.08, 18.6, 0.280, 0.310, 0.0), 0.2)]})
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
# thin PHY_1V8 B south loop hw0.3 -> hw0.15
fat = [it for it in pool[2] if it[1] == 'PHY_1V8' and it[0] == 'seg'
       and abs(it[2][4] - 0.3) < 1e-9 and it[2][1] < 15.5]
print('thinning south-loop segs:', len(fat), flush=True)
rip_items(fat)
add_items({2: [('seg', 'PHY_1V8',
                (it[2][0], it[2][1], it[2][2], it[2][3], 0.15), it[3])
               for it in fat]})


import numpy as np, math
box = (74.0, 78.0, 9.0, 15.0)
X0, X1, Y0, Y1 = box
step = 0.05
xs = np.arange(X0, X1 + 1e-9, step)
ys = np.arange(Y0, Y1 + 1e-9, step)
GXm, GYm = np.meshgrid(xs, ys)

def df(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = GXm - cx, GYm - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = GXm - x1, GYm - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    return np.hypot(GXm - d[0], GYm - d[1]) - d[2]

f = np.full(GXm.shape, 9.9)
for it in pool[2]:
    if it[1] == 'ULPI_STP':
        continue
    req = max(0.2, it[3])
    f = np.minimum(f, df(it) - req)
for y in (11.05, 11.0, 10.95, 10.9, 10.85, 10.8):
    iy = int(round((y - Y0) / step))
    row = f'y={y}: '
    for x in (76.2, 76.25, 76.3, 76.35, 76.4):
        ix = int(round((x - X0) / step))
        row += f'{f[iy, ix]:+.3f} '
    print(row, flush=True)
