import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
box = (75.0, 77.0, 17.0, 19.0)
for label, g in (('W (75.9,17.99)', (2, 75.9, 17.99)),
                 ('S (76.065,17.8)', (2, 76.065, 17.8)),
                 ('E (76.2,17.99)', (2, 76.2, 17.99)),
                 ('N (76.065,18.2)', (2, 76.065, 18.2)),
                 ('SW (75.9,18.15)', (2, 75.9, 18.15))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', ((2,), 76.065, 17.99), g, hw=0.10)
    print(f'{label}:', 'FOUND' if J else 'NONE', flush=True)
# inspect the closure for the field
astar = make_astar(box, 0.05)
print('closure vars:', [c for c in astar.__code__.co_freevars], flush=True)
cells = dict(zip(astar.__code__.co_freevars, astar.__closure__))
for k, v in cells.items():
    print(' ', k, type(v), (len(v) if hasattr(v, '__len__') else v), flush=True)
