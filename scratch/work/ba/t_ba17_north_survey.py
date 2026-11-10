"""t_ba17: survey for the C22-north configuration.
1) PHY_1V8's full item list (all layers) -- the route map.
2) Via nest in x[73,80] y[7,12]: every via, all nets.
3) All items in x[73.5,79.5] y[7.5,11.5] on F and B."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp252.kicad_pcb')
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
print('--- PHY_1V8 items, all layers ---')
for l in range(3):
    for it in pool[l]:
        if it[1] != 'PHY_1V8':
            continue
        d = it[2]
        if it[0] == 'seg':
            print(f'  {LAYN[l]} seg ({d[0]:.2f},{d[1]:.2f})->'
                  f'({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')
        elif it[0] == 'via':
            print(f'  {LAYN[l]} via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}')
        else:
            print(f'  {LAYN[l]} pad ({d[0]:.2f},{d[1]:.2f})')
print('--- via nest x[73,80] y[7,12] ---')
seen = set()
for l in range(3):
    for it in pool[l]:
        if it[0] != 'via':
            continue
        d = it[2]
        key = (it[1], round(d[0], 2), round(d[1], 2))
        if 73 <= d[0] <= 80 and 7 <= d[1] <= 12 and key not in seen:
            seen.add(key)
            print(f'  {it[1]} via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}')
print('--- items x[73.5,79.5] y[7.5,11.5], F and B ---')
for l in (0, 2):
    for it in pool[l]:
        cc = C(it)
        if 73.5 <= cc[0] <= 79.5 and 7.5 <= cc[1] <= 11.5:
            d = it[2]
            if it[0] == 'seg':
                print(f'  {LAYN[l]} {it[1]} seg ({d[0]:.2f},{d[1]:.2f})->'
                      f'({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')
            elif it[0] == 'via':
                print(f'  {LAYN[l]} {it[1]} via ({d[0]:.2f},{d[1]:.2f})'
                      f' r{d[2]}')
            else:
                print(f'  {LAYN[l]} {it[1]} pad ({d[0]:.2f},{d[1]:.2f})')
print('=== done ===')
