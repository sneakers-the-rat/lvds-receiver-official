import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
c20 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.5) < 0.01 and it[2][0] in (75.725, 77.275)]
rip_items(c20)
add_items({0: [('pad', 'XI', (75.72, 18.75, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (76.68, 18.75, 0.280, 0.310, 0.0), 0.2)]})
box = (67.0, 78.5, -4.0, 19.5)
cur = ((2,), 76.065, 17.99)
legs = []
for label, g in (('B (75.5,16.9)', (2, 75.5, 16.9)),
                 ('B (73.9,16.9)', (2, 73.9, 16.9)),
                 ('B (72.6,16.6)', (2, 72.6, 16.6)),
                 ('B (72.3,15.2)', (2, 72.3, 15.2)),
                 ('B (71.35,13.6)', (2, 71.35, 13.6)),
                 ('B (71.5,11.6)', (2, 71.5, 11.6)),
                 ('B (70.0,6.0)', (2, 70.0, 6.0)),
                 ('B (68.8,1.0)', (2, 68.8, 1.0)),
                 ('B (70.5,-2.25)', (2, 70.5, -2.25)),
                 ('F pad', (0, 71.3375, -2.25))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', cur, g, hw=0.10)
    print(f'stage -> {label}:', 'FOUND' if J else 'NONE',
          ('vias=' + str(J['vias'])) if J else '', flush=True)
    if not J:
        break
    legs.append(J)
    cur = ((g[0],), g[1], g[2])
if len(legs) == 10:
    json.dump({'legs': legs},
              open('scratch/work/ax/stp_legs_ax167.json', 'w'))
    print('STP HAUL COMPLETE', flush=True)
