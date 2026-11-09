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
                 and abs(it[2][1] - 17.685) < 0.01)
             or (abs(it[2][0] - 76.487) < 0.01
                 and abs(it[2][1] - 9.139) < 0.01))]
rip_items(arm)
# thin PHY_1V8 B south loop hw0.3 -> hw0.15 AND shift its vertical
# east x76.8 -> x76.95 (corner follows), opening the STP descent lens
fat = [it for it in pool[2] if it[1] == 'PHY_1V8' and it[0] == 'seg'
       and abs(it[2][4] - 0.3) < 1e-9 and it[2][1] < 15.5]
print('re-laying south-loop segs:', len(fat), flush=True)
for it in fat:
    print('   ', L.fmt_it(it), flush=True)
rip_items(fat)
newsegs = []
for it in fat:
    x1, y1, x2, y2, hw = it[2]
    pts = []
    for (x, y) in ((x1, y1), (x2, y2)):
        if abs(x - 76.8) < 0.01:
            x = 76.95
            if abs(y - 10.988) < 0.01:
                y = 11.05
        if abs(x - 77.35) < 0.01 and abs(y - 10.0) < 0.01:
            x, y = 77.45, 10.1
        pts.append((x, y))
    newsegs.append(('seg', 'PHY_1V8',
                    (pts[0][0], pts[0][1], pts[1][0], pts[1][1], 0.15),
                    it[3]))
add_items({2: newsegs})
# move PHY_1V8's south via east (77.869,10.056) -> (77.98,10.02): rip the
# via, its F feed seg and the re-laid B seg; re-add at the new site
stub = [it for it in pool[0] if it[1] == 'PHY_1V8' and it[0] == 'seg'
        and abs(it[2][2] - 77.869) < 0.01 and abs(it[2][3] - 10.056) < 0.01]
bseg = [it for it in pool[2] if it[1] == 'PHY_1V8' and it[0] == 'seg'
        and abs(it[2][0] - 77.869) < 0.01 and abs(it[2][1] - 10.056) < 0.01]
via = [it for it in pool[2] if it[0] == 'via'
       and abs(it[2][0] - 77.869) < 0.01 and abs(it[2][1] - 10.056) < 0.01]
print('stub rip:', [(L.fmt_it(i)) for i in stub + bseg + via], flush=True)
rip_items(stub + bseg + via)
add_items({0: [('seg', 'PHY_1V8', (77.25, 10.75, 77.98, 10.02, 0.1), 0.25)],
           2: [('seg', 'PHY_1V8', (77.98, 10.02, 77.45, 10.1, 0.15), 0.25),
               ('via', 'PHY_1V8', (77.98, 10.02, 0.25), 0.25)]})


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

for pt in ((73.5, -0.6), (73.3, -0.45), (72.7, -0.4), (72.45, -0.45),
           (73.6, -0.9), (72.0, -0.6), (73.45, -1.05)):
    vals = sorted(((df(it, *pt) - max(0.2, it[3]), it)
                   for it in pool[0] if it[1] != 'ULPI_STP'))
    print(f'F {pt}: G={vals[0][0]:+.3f}', L.fmt_it(vals[0][1]),
          '| 2nd', f"{vals[1][0]:+.3f}", L.fmt_it(vals[1][1]), flush=True)
