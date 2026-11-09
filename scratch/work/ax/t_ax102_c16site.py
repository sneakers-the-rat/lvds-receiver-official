import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
print('== ALL items in (74,79.5,6,10.5) by layer:', flush=True)
for lay in range(3):
    seen = set()
    for it in pool[lay]:
        d = it[2]
        if 74 < d[0] < 79.5 and 6 < d[1] < 10.5:
            s = 'L%d ' % lay + L.fmt_it(it)
            if s not in seen:
                seen.add(s)
                print('  ', s, flush=True)
print('== GND items in (75.5,78,8.5,11):', flush=True)
seen = set()
for lay in range(3):
    for it in pool[lay]:
        if it[1] != 'GND':
            continue
        d = it[2]
        if 75.5 < d[0] < 78 and 8.5 < d[1] < 11:
            s = 'L%d ' % lay + L.fmt_it(it)
            if s not in seen:
                seen.add(s)
                print('  ', s, flush=True)
