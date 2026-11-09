import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
for net in ('XO',):
    fs = fragsets(pool, net, (60.0, 100.0, -30.0, 45.0))
    print(f'{net}: {len(fs)} fragment(s)', flush=True)
    for f in fs:
        print('   size', len(f['items']), 'terms', f['terms'], flush=True)
    seen = set()
    for lay in range(3):
        for it in pool[lay]:
            if it[1] == net:
                d = it[2]
                if 70 < d[0] < 80 and 7 < d[1] < 18:
                    s = 'L%d ' % lay + L.fmt_it(it)
                    if s not in seen:
                        seen.add(s)
                        print('  ', s, flush=True)
