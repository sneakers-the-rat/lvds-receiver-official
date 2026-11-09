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

box = (66.0, 78.5, -4.0, 19.5)
cur = ((2,), 76.065, 17.99)
legs = []
for label, g in (('B (75.5,16.9)', (2, 75.5, 16.9)),
                 ('B (73.9,16.9)', (2, 73.9, 16.9)),
                 ('B (71.3,17.6)', (2, 71.3, 17.6)),
                 ('I (70.05,17.2)', (1, 70.05, 17.2)),
                 ('I (68.9,16.6)', (1, 68.9, 16.6)),
                 ('I (67.7,14.5)', (1, 67.7, 14.5)),
                 ('B (67.7,11.0)', (2, 67.7, 11.0)),
                 ('B (68.6,6.0)', (2, 68.6, 6.0)),
                 ('B (68.8,1.0)', (2, 68.8, 1.0)),
                 ('B (70.3,-2.25)', (2, 70.3, -2.25)),
                 ('F pad', (0, 71.3375, -2.25))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', cur, g, hw=0.10)
    print(f'STP stage -> {label}:', 'FOUND' if J else 'NONE',
          ('vias=' + str(J['vias'])) if J else '', flush=True)
    if not J:
        break
    legs.append(J)
    cur = ((g[0],), g[1], g[2])
out = {}
if len(legs) == 11:
    out['stp_legs'] = legs
    print('STP HAUL COMPLETE', flush=True)
json.dump(out, open('scratch/work/ax/design214_ax180.json', 'w'))
