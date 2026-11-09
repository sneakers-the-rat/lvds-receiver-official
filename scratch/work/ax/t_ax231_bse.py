import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
from collections import Counter
cnt = Counter()
for it in pool[2]:
    d = it[2]
    if it[0] == 'seg' and max(d[0], d[2]) > 73 and min(d[0], d[2]) < 78.5 \
            and max(d[1], d[3]) > -1 and min(d[1], d[3]) < 7:
        cnt[it[1]] += 1
    if it[0] == 'via' and 73 < d[0] < 78.5 and -1 < d[1] < 7:
        cnt[it[1] + ' via'] += 1
print(cnt, flush=True)
for net in ('CAP_CLK', 'CAP_DATA', 'ULPI_CK', 'ULPI_D0', 'BIST_DRV0'):
    print(f'--- {net} B items:', flush=True)
    for it in pool[2]:
        if it[1] != net:
            continue
        d = it[2]
        if it[0] == 'seg' and max(d[0], d[2]) > 73 and min(d[0], d[2]) < 78.5 \
                and max(d[1], d[3]) > -1 and min(d[1], d[3]) < 7:
            print('  ', L.fmt_it(it), flush=True)
        if it[0] == 'via' and 73 < d[0] < 78.5 and -1 < d[1] < 7:
            print('  ', L.fmt_it(it), flush=True)
