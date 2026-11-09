import sys
sys.path.insert(0, 'scratch/work/ax')
import t_ax0_pre as P
print('BOARD before patch:', P.BOARD, flush=True)
P.BOARD = 'hw/pdlvds_rx.exp242.kicad_pcb'
from t_ax0_pre import *  # noqa
pool = load_board_pool()
hits = [it for l in range(3) for it in pool[l]
        if it[0] == 'via' and abs(it[2][0] - 69.225) < 0.01
        and abs(it[2][1] + 9.075) < 0.01]
print('pool vias at (69.225,-9.075):', hits, flush=True)
hits2 = [it for it in pool[0] if it[1] == 'I2C_SCL'
         and abs(it[2][1] + 1.75) < 0.3 and it[0] == 'seg']
print('SCL F segs near y-1.75:', len(hits2), flush=True)
import t_ax0_pre
print('module BOARD now:', t_ax0_pre.BOARD, flush=True)
