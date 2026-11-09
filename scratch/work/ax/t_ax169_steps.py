import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
box = (71.0, 78.5, 8.0, 19.5)
for label, g in (('W (73.7,16.9)', (2, 73.7, 16.9)),
                 ('N (73.9,17.1)', (2, 73.9, 17.1)),
                 ('NW (73.7,17.1)', (2, 73.7, 17.1)),
                 ('NW (73.5,17.2)', (2, 73.5, 17.2)),
                 ('W (73.4,16.9)', (2, 73.4, 16.9)),
                 ('N (73.9,17.3)', (2, 73.9, 17.3))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', ((2,), 73.9, 16.9), g, hw=0.10)
    print(f'{label}:', 'FOUND' if J else 'NONE', flush=True)
