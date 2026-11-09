import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
from collections import Counter
cnt = Counter()
for it in pool[1]:
    d = it[2]
    if it[0] == 'seg' and max(d[0], d[2]) > 67 and min(d[0], d[2]) < 75 \
            and max(d[1], d[3]) > -3.5 and min(d[1], d[3]) < 0.5:
        cnt[it[1]] += 1
    if it[0] == 'via' and 67 < d[0] < 75 and -3.5 < d[1] < 0.5:
        cnt[it[1] + ' via'] += 1
print(cnt, flush=True)
for net in cnt:
    n = net.replace(' via', '')
    print(f'--- {n} In2:', flush=True)
    for it in pool[1]:
        if it[1] != n:
            continue
        d = it[2]
        if it[0] == 'seg' and max(d[0], d[2]) > 67 and min(d[0], d[2]) < 75 \
                and max(d[1], d[3]) > -3.5 and min(d[1], d[3]) < 0.5:
            print('  ', L.fmt_it(it), flush=True)
        if it[0] == 'via' and 67 < d[0] < 75 and -3.5 < d[1] < 0.5:
            print('  ', L.fmt_it(it), flush=True)
