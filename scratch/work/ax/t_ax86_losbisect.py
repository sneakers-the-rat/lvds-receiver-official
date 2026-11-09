import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
FULL = load_board_pool('hw/pdlvds_rx.exp248.kicad_pcb')

def ablate(pool, pred):
    return [[it for it in pool[l] if not pred(it)] for l in range(3)]

SDA_WEAVE = lambda it: it[1] == 'I2C_SDA' and it[0] == 'seg' \
    and it[2][0] < 71.0 and it[2][1] > 30.0
WALL = lambda it: it[1] == '+3V3D_CDR' and it[0] == 'seg' \
    and abs(it[2][0] - 69.625) < 0.01 and it[2][1] > 35.0
pool = ablate(FULL, lambda it: SDA_WEAVE(it) or WALL(it))
globals()['pool'] = pool
for m in list(sys.modules.values()):
    if hasattr(m, 'pool'):
        try:
            m.__dict__['pool'] = pool
        except Exception:
            pass
goals = [
    ('(71,35.9) F', (0, 71.0, 35.9), (66.0, 76.0, 30.0, 39.0)),
    ('(74,30) any', ((0, 1, 2), 74.0, 30.0), (66.0, 80.0, 24.0, 39.0)),
    ('(76,22) any', ((0, 1, 2), 76.0, 22.0), (66.0, 82.0, 16.0, 39.0)),
    ('(79,12) any', ((0, 1, 2), 79.0, 12.0), (66.0, 85.0, 6.0, 39.0)),
    ('(82,6) B', (2, 82.0, 6.0), (66.0, 88.0, 0.0, 39.0)),
    ('(85,5) B big', (2, 85.0, 5.0), (66.0, 95.0, -1.0, 39.0)),
]
for label, goal, box in goals:
    astar = make_astar(box, 0.05)
    J = astar('CDR_LOS', ((0,), 68.6875, 36.5), goal, hw=0.10)
    print(f'{label}:', 'FOUND' if J else 'NONE',
          ('vias ' + str(J['vias'])) if J else '', flush=True)
