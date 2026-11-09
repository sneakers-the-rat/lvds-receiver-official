import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import t_ax0_pre as P
FULL = load_board_pool('hw/pdlvds_rx.exp248.kicad_pcb')

def set_pool(pred):
    abl = {l: [it for it in FULL[l] if not pred(it)] for l in range(3)}
    for _d in P._ns.values():
        _d['pool'] = abl
    return abl

def near(it):
    d = it[2]
    return it[1] != 'CDR_LOS' and 66 < d[0] < 74 and 33 < d[1] < 40

set_pool(near)
astar = make_astar((66.0, 76.0, 30.0, 39.0), 0.05)
J = astar('CDR_LOS', ((0,), 68.6875, 36.5), (0, 71.0, 35.9), hw=0.10)
print('CONTROL (all foreign near U4 removed):',
      'FOUND' if J else 'NONE', flush=True)

SDA_WEAVE = lambda it: it[1] == 'I2C_SDA' and it[0] == 'seg' \
    and it[2][0] < 71.0 and it[2][1] > 30.0
WALL = lambda it: it[1] == '+3V3D_CDR' and it[0] == 'seg' \
    and abs(it[2][0] - 69.625) < 0.01 and it[2][1] > 35.0
SCL_IN2 = lambda it: it[1] == 'I2C_SCL' and it[0] == 'seg' \
    and it[2][0] > 70.0 and it[2][1] > 30.0
cases = [
    ('none', lambda it: False, (0, 71.0, 35.9), (66.0, 76.0, 30.0, 39.0)),
    ('-SDAweave', SDA_WEAVE, (0, 71.0, 35.9), (66.0, 76.0, 30.0, 39.0)),
    ('-WALL', WALL, (0, 71.0, 35.9), (66.0, 76.0, 30.0, 39.0)),
    ('-SDA-WALL', lambda it: SDA_WEAVE(it) or WALL(it),
     (0, 71.0, 35.9), (66.0, 76.0, 30.0, 39.0)),
    ('-SDA-WALL-SCL', lambda it: SDA_WEAVE(it) or WALL(it) or SCL_IN2(it),
     (0, 71.0, 35.9), (66.0, 76.0, 30.0, 39.0)),
    ('-SDA-WALL full', lambda it: SDA_WEAVE(it) or WALL(it),
     (2, 85.0, 5.0), (66.0, 95.0, -1.0, 39.0)),
    ('-SDA-WALL-SCL full',
     lambda it: SDA_WEAVE(it) or WALL(it) or SCL_IN2(it),
     (2, 85.0, 5.0), (66.0, 95.0, -1.0, 39.0)),
]
for label, pred, goal, box in cases:
    set_pool(pred)
    astar = make_astar(box, 0.05)
    J = astar('CDR_LOS', ((0,), 68.6875, 36.5), goal, hw=0.10)
    print(f'{label}:', 'FOUND' if J else 'NONE',
          ('vias ' + str(J['vias'])) if J else '', flush=True)
