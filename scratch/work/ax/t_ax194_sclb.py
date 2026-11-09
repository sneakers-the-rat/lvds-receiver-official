import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for it in pool[2]:
    if it[1] == 'I2C_SCL':
        d = it[2]
        if it[0] == 'seg' and max(d[0], d[2]) > 74.0 and min(d[1], d[3]) > 6.0:
            print('  ', L.fmt_it(it), flush=True)
        if it[0] == 'via' and d[0] > 74.0 and d[1] > 6.0:
            print('  ', L.fmt_it(it), flush=True)
