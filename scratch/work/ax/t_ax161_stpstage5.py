import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
c20 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.5) < 0.01 and it[2][0] in (75.725, 77.275)]
rip_items(c20)
add_items({0: [('pad', 'XI', (75.72, 18.75, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (76.68, 18.75, 0.280, 0.310, 0.0), 0.2)]})
box = (69.0, 78.5, -4.0, 19.5)
cur = ((2,), 76.065, 17.99)
legs = []
for label, g in (('B (76.35,18.1)', (2, 76.35, 18.1)),
                 ('B (76.15,13.5)', (2, 76.15, 13.5)),
                 ('B (76.15,11.0)', (2, 76.15, 11.0)),
                 ('B (74.3,9.7)', (2, 74.3, 9.7)),
                 ('B (72.5,5)', (2, 72.5, 5.0)),
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
if len(legs) == 7:
    json.dump({'legs': legs},
              open('scratch/work/ax/stp_legs_ax161.json', 'w'))
    print('STP HAUL COMPLETE', flush=True)
