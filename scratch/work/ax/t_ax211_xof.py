import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for net in ('XO', 'RBIAS'):
    print(f'--- {net} F items in (69,75,17.5,22):', flush=True)
    for it in pool[0]:
        if it[1] != net:
            continue
        d = it[2]
        if it[0] == 'seg' and max(d[0], d[2]) > 69 and min(d[0], d[2]) < 75 \
                and max(d[1], d[3]) > 17.5 and min(d[1], d[3]) < 22:
            print('  ', L.fmt_it(it), flush=True)
        if it[0] == 'via' and 69 < d[0] < 75 and 17.5 < d[1] < 22:
            print('  ', L.fmt_it(it), flush=True)
