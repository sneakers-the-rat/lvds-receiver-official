import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for net in ('RBIAS', 'XO', 'ULPI_NXT'):
    print(f'--- {net} In2 items in (70,78,16,21):', flush=True)
    for it in pool[1]:
        if it[1] != net:
            continue
        d = it[2]
        if it[0] == 'seg' and max(d[0], d[2]) > 70 and min(d[0], d[2]) < 78 \
                and max(d[1], d[3]) > 16 and min(d[1], d[3]) < 21:
            print('  ', L.fmt_it(it), flush=True)
        if it[0] == 'via' and 70 < d[0] < 78 and 16 < d[1] < 21:
            print('  ', L.fmt_it(it), flush=True)
