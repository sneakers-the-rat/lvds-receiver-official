import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for l, nm in ((2, 'B'), (0, 'F'), (1, 'In2')):
    print(f'--- SDA {nm} items in (67,73,-11,3):', flush=True)
    for it in pool[l]:
        if it[1] != 'I2C_SDA':
            continue
        d = it[2]
        if it[0] == 'seg' and max(d[0], d[2]) > 67 and min(d[0], d[2]) < 73 \
                and max(d[1], d[3]) > -11 and min(d[1], d[3]) < 3:
            print('  ', L.fmt_it(it), flush=True)
        if it[0] == 'via' and 67 < d[0] < 73 and -11 < d[1] < 3:
            print('  ', L.fmt_it(it), flush=True)
