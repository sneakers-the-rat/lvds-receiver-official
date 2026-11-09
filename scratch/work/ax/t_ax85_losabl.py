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
SCL_IN2 = lambda it: it[1] == 'I2C_SCL' and it[0] == 'seg' \
    and it[2][0] > 70.0 and it[2][1] > 30.0

cases = [
    ('none', lambda it: False),
    ('-SDAweave', SDA_WEAVE),
    ('-WALL', WALL),
    ('-SDAweave-WALL', lambda it: SDA_WEAVE(it) or WALL(it)),
    ('-SDAweave-WALL-SCLin2', lambda it: SDA_WEAVE(it) or WALL(it)
     or SCL_IN2(it)),
]
for label, pred in cases:
    pool = ablate(FULL, pred)
    globals()['pool'] = pool
    for m in list(sys.modules.values()):
        if hasattr(m, 'pool'):
            try:
                m.__dict__['pool'] = pool
            except Exception:
                pass
    astar = make_astar((66.0, 95.0, -1.0, 39.0), 0.05)
    J = astar('CDR_LOS', ((0,), 68.6875, 36.5), (2, 85.0, 5.0), hw=0.10)
    print(f'{label}:', 'FOUND' if J else 'NONE',
          ('vias ' + str(J['vias'])) if J else '', flush=True)
