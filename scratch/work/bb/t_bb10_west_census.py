"""t_bb10: full census west/south-west of U7 on exp254.
Box x[72.6,75.6] y[11.0,19.6], all nets, all layers (compact:
only seg endpoints/vias/pads, deduped). Plus DM_PHY and ULPI_NXT
items in x[72.6,76.4] y[15.5,20.5]."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

BOARD = 'hw/pdlvds_rx.exp254.kicad_pcb'
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)

def show(l, it):
    d = it[2]
    if it[0] == 'seg':
        return f'  {LAYN[l]:3} {it[1]:9} seg ({d[0]:.3f},{d[1]:.3f})->({d[2]:.3f},{d[3]:.3f}) w{d[4]}'
    if it[0] == 'via':
        return f'  {LAYN[l]:3} {it[1]:9} via ({d[0]:.3f},{d[1]:.3f}) r{d[2]}'
    return f'  {LAYN[l]:3} {it[1]:9} pad ({d[0]:.3f},{d[1]:.3f}) hx{d[2]} hy{d[3]}'

seen = set()
print('--- west box x[72.6,75.6] y[11.0,19.6] ---')
for l in range(3):
    for it in pool[l]:
        if it[0] == 'via':
            key = ('via', it[1], it[2])
            if key in seen:
                continue
            seen.add(key)
        cc = C(it)
        if 72.6 <= cc[0] <= 75.6 and 11.0 <= cc[1] <= 19.6:
            print(show(l, it))
print('--- DM_PHY / ULPI_NXT x[72.6,76.4] y[15.5,20.5] ---')
seen = set()
for l in range(3):
    for it in pool[l]:
        if it[1] not in ('DM_PHY', 'ULPI_NXT', 'DP_PHY'):
            continue
        if it[0] == 'via':
            key = ('via', it[1], it[2])
            if key in seen:
                continue
            seen.add(key)
        cc = C(it)
        if 72.6 <= cc[0] <= 76.4 and 15.5 <= cc[1] <= 20.5:
            print(show(l, it))
