import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for l in (1, 2):
    print(f'== layer {l} items (73.8,76.4,11.5,15.5):', flush=True)
    for it in pool[l]:
        d = it[2]
        if 73.8 < d[0] < 76.4 and 11.5 < d[1] < 15.5:
            print('  ', L.fmt_it(it), flush=True)
