import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp248.kicad_pcb')
tests = [
    ('U4 -> (74,32)', ((0,), 68.6875, 36.5), (0, 74.0, 32.0),
     (66.0, 80.0, 28.0, 39.0)),
    ('U4 -> (70,20)', ((0,), 68.6875, 36.5), (0, 70.0, 20.0),
     (66.0, 76.0, 16.0, 39.0)),
    ('U4 -> (69,8)', ((0,), 68.6875, 36.5), (2, 69.0, 8.0),
     (66.0, 74.0, 4.0, 39.0)),
    ('U6.75 -> (95,10)', ((0,), 92.6625, 1.75), (0, 95.0, 10.0),
     (88.0, 97.0, -2.0, 14.0)),
    ('U6.75 -> (90,5) B', ((0, 1, 2), 92.6625, 1.75), (2, 90.0, 5.0),
     (84.0, 96.0, -2.0, 10.0)),
    ('U6.75 -> (85,5) B', ((0, 1, 2), 92.6625, 1.75), (2, 85.0, 5.0),
     (80.0, 96.0, -2.0, 10.0)),
]
for label, start, goal, box in tests:
    astar = make_astar(box, 0.05)
    J = astar('CDR_LOS', start, goal, hw=0.10)
    print(f'{label}:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        print('   vias:', J['vias'], flush=True)
