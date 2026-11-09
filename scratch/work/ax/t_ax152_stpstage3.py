import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
c20 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.5) < 0.01 and it[2][0] in (75.725, 77.275)]
rip_items(c20)
add_items({0: [('pad', 'XI', (75.72, 18.75, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (76.68, 18.75, 0.280, 0.310, 0.0), 0.2)]})
add_items({l: [('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]
           for l in range(3)})
box = (69.0, 78.5, -4.0, 19.0)
cur = ((1,), 76.065, 17.99)
legs = []
for label, g in (('I (76.06,14)', (1, 76.06, 14.0)),
                 ('I (74.2,12.5)', (1, 74.2, 12.5)),
                 ('I (74.2,7)', (1, 74.2, 7.0)),
                 ('I (73,2)', (1, 73.0, 2.0)),
                 ('B (71.5,-1)', (2, 71.5, -1.0)),
                 ('F pad', (0, 71.3375, -2.25))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', cur, g, hw=0.10)
    print(f'stage -> {label}:', 'FOUND' if J else 'NONE',
          ('vias=' + str(J['vias'])) if J else '', flush=True)
    if not J:
        break
    legs.append(J)
    cur = ((g[0],), g[1], g[2])
if len(legs) == 6:
    print('FULL STP HAUL FOUND in 6 legs', flush=True)
