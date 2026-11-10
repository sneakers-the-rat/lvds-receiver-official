"""t_ba8: In2 fence dump for x[69,78] y[9,20.5] on exp252
(excluding nothing — all nets), compact: one line per item."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp252.kicad_pcb')
for it in pool[1]:
    cc = C(it)
    if 69 <= cc[0] <= 78 and 9 <= cc[1] <= 20.5:
        d = it[2]
        if it[0] == 'seg':
            print(f'In2 {it[1]} seg ({d[0]:.2f},{d[1]:.2f})->'
                  f'({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')
        elif it[0] == 'via':
            print(f'In2 {it[1]} via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}')
        elif it[0] == 'pad':
            print(f'In2 {it[1]} pad ({d[0]:.2f},{d[1]:.2f})')
print('=== done ===')
