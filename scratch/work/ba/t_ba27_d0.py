"""t_ba27: ULPI_D0 complete item list in x[75,79.5]
y[6.5,12] on F and B (the staircase's true shape)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp252.kicad_pcb')
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
for l in (0, 2, 1):
    print(f'--- D0 {LAYN[l]} ---')
    out = []
    for it in pool[l]:
        if it[1] != 'ULPI_D0':
            continue
        cc = C(it)
        if 75 <= cc[0] <= 79.5 and 6.5 <= cc[1] <= 12:
            d = it[2]
            if it[0] == 'seg':
                out.append(f'  seg ({d[0]:.2f},{d[1]:.2f})->'
                           f'({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')
            elif it[0] == 'via':
                out.append(f'  via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}')
            else:
                out.append(f'  pad ({d[0]:.2f},{d[1]:.2f})')
    for s in sorted(set(out)):
        print(s)
print('=== done ===')
