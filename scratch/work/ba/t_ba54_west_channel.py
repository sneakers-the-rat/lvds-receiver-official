"""t_ba54: west channel census on exp253: B items of
ULPI_DIR, PHY_1V8A, ULPI_NXT, GND in x[73.5,76.0]
y[12.0,19.5]; XO F staircase-foot segs x[75.9,76.6]
y[9.7,10.5]; STP B descent segs x[76.0,76.6] y[8.8,13.6]."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp253.kicad_pcb')
for net in ('ULPI_DIR', 'PHY_1V8A', 'ULPI_NXT'):
    print(f'--- {net} B x[73.5,76.0] y[12.0,19.5] ---')
    seen = set()
    for it in pool[2]:
        if it[1] != net:
            continue
        cc = C(it)
        if 73.5 <= cc[0] <= 76.0 and 12.0 <= cc[1] <= 19.5:
            d = it[2]
            if it[0] == 'seg':
                s = f'  seg ({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f})'
            elif it[0] == 'via':
                s = f'  via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}'
            else:
                s = f'  pad ({d[0]:.2f},{d[1]:.2f})'
            if s not in seen:
                seen.add(s)
                print(s)
    print(f'  ({len(seen)} unique)')
print('--- XO F staircase foot x[75.9,76.6] y[9.7,10.5] ---')
for it in pool[0]:
    if it[1] != 'XO' or it[0] != 'seg':
        continue
    cc = C(it)
    if 75.9 <= cc[0] <= 76.6 and 9.7 <= cc[1] <= 10.5:
        d = it[2]
        print(f'  seg ({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f})')
print('--- ULPI_STP B descent x[76.0,76.6] y[8.8,13.6] ---')
n = 0
for it in pool[2]:
    if it[1] != 'ULPI_STP':
        continue
    cc = C(it)
    if 76.0 <= cc[0] <= 76.6 and 8.8 <= cc[1] <= 13.6:
        n += 1
        if it[0] == 'via':
            print(f"  via ({it[2][0]:.2f},{it[2][1]:.2f}) r{it[2][2]}")
print(f'  ({n} items incl segs)')
print('=== done ===')
