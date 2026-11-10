"""t_ba47: XI drop corridor census on exp253: items of
1V8A, ULPI_STP, XO, +3V3A, PHY_1V8, XI on B and F in
x[74.2,77.0] y[9.8,19.0] (centre within box)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp253.kicad_pcb')
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
NETS = ('PHY_1V8A', 'ULPI_STP', 'XO', '+3V3A', 'PHY_1V8', 'XI')
for l in (2, 0):
    print(f'===== {LAYN[l]} =====')
    for net in NETS:
        items = []
        for it in pool[l]:
            if it[1] != net:
                continue
            cc = C(it)
            if 74.2 <= cc[0] <= 77.0 and 9.8 <= cc[1] <= 19.0:
                d = it[2]
                if it[0] == 'seg':
                    items.append(f'  seg ({d[0]:.2f},{d[1]:.2f})->'
                                 f'({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')
                elif it[0] == 'via':
                    items.append(f'  via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}')
                else:
                    items.append(f'  pad ({d[0]:.2f},{d[1]:.2f})')
        if items:
            print(f'-- {net} ({len(items)}) --')
            for s in sorted(set(items)):
                print(s)
print('=== done ===')
