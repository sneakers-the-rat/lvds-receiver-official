import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for net in ('ULPI_CK', 'ULPI_DIR'):
    print(f'== {net} items (72,80,3,20):', flush=True)
    for l in range(3):
        for it in pool[l]:
            if it[1] != net:
                continue
            d = it[2]
            if 72 < d[0] < 80 and 3 < d[1] < 20:
                print('  ', 'FIB'[l], L.fmt_it(it), flush=True)
