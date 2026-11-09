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


box = (74.0, 78.0, 9.0, 15.0)
for label, g in (('B (76.3,11.0)', (2, 76.3, 11.0)),
                 ('B (76.3,10.85)', (2, 76.3, 10.85)),
                 ('B (76.05,10.15)', (2, 76.05, 10.15)),
                 ('B (75.8,10.15)', (2, 75.8, 10.15))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', ((2,), 76.15, 13.5), g, hw=0.10)
    print(f'{label}:', 'FOUND' if J else 'NONE', flush=True)
