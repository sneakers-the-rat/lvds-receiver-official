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


box = (64.0, 79.5, -4.0, 20.5)
for goal in ((2, 77.6, 9.55), (2, 77.65, 9.5), (2, 77.8, 9.3),
             (2, 77.7, 9.45)):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', ((2,), 77.45, 9.55), goal, hw=0.10)
    print('goal', goal, ':', 'FOUND' if J else 'NONE', flush=True)
