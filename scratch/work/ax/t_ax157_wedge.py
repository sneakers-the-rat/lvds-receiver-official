import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
box = (73.0, 78.0, 16.0, 20.5)
for label, g in (('B (75.9,18.2)', (2, 75.9, 18.2)),
                 ('B (75.6,18.3)', (2, 75.6, 18.3)),
                 ('B (75.3,18.3)', (2, 75.3, 18.3)),
                 ('B (74.9,18.5)', (2, 74.9, 18.5)),
                 ('B (75.9,17.6)', (2, 75.9, 17.6)),
                 ('B (76.3,18.4)', (2, 76.3, 18.4))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', ((2,), 76.065, 17.99), g, hw=0.10)
    print(f'{label}:', 'FOUND' if J else 'NONE', flush=True)
