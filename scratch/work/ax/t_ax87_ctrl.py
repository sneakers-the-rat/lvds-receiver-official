import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
FULL = load_board_pool('hw/pdlvds_rx.exp248.kicad_pcb')

def ablate(pool, pred):
    return [[it for it in pool[l] if not pred(it)] for l in range(3)]

def near(it):
    d = it[2]
    return it[1] != 'CDR_LOS' and 66 < d[0] < 74 and 33 < d[1] < 40

pool = ablate(FULL, near)
print('ablated counts per layer:',
      [len(FULL[l]) - len(pool[l]) for l in range(3)], flush=True)
globals()['pool'] = pool
for m in list(sys.modules.values()):
    if hasattr(m, 'pool'):
        try:
            m.__dict__['pool'] = pool
        except Exception:
            pass
import t_ax0_pre
print('t_ax0_pre.pool is ablated:', t_ax0_pre.pool is pool, flush=True)
astar = make_astar((66.0, 76.0, 30.0, 39.0), 0.05)
J = astar('CDR_LOS', ((0,), 68.6875, 36.5), (0, 71.0, 35.9), hw=0.10)
print('control U4 -> (71,35.9):', 'FOUND' if J else 'NONE', flush=True)
