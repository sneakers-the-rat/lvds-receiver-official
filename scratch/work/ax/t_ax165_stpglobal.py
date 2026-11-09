import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
c20 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.5) < 0.01 and it[2][0] in (75.725, 77.275)]
rip_items(c20)
add_items({0: [('pad', 'XI', (75.72, 18.75, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (76.68, 18.75, 0.280, 0.310, 0.0), 0.2)]})
box = (56.0, 80.0, -6.0, 25.0)
for label, start in (('B dive', ((2,), 76.065, 17.99)),
                     ('I dive', ((1,), 76.065, 17.99)),
                     ('F stub', ((0,), 76.25, 16.95))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', start, (0, 71.3375, -2.25), hw=0.10)
    print(f'{label}:', 'FOUND vias=' + str(J['vias']) if J else 'NONE',
          flush=True)
