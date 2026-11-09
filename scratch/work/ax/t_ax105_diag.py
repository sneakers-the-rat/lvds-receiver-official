import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
print('== C23 district ALL items (68.5,72.5,12.5,17):', flush=True)
for lay in range(3):
    seen = set()
    for it in pool[lay]:
        d = it[2]
        if 68.5 < d[0] < 72.5 and 12.5 < d[1] < 17:
            s = 'L%d ' % lay + L.fmt_it(it)
            if s not in seen:
                seen.add(s)
                print('  ', s, flush=True)
print('== XO corridor F items (72,77.5,9.8,12.8):', flush=True)
seen = set()
for it in pool[0]:
    d = it[2]
    if 72 < d[0] < 77.5 and 9.8 < d[1] < 12.8:
        s = L.fmt_it(it)
        if s not in seen:
            seen.add(s)
            print('  ', s, flush=True)
print('== XO corridor In2 items (72,77.5,9.8,12.8):', flush=True)
seen = set()
for it in pool[1]:
    d = it[2]
    if 72 < d[0] < 77.5 and 9.8 < d[1] < 12.8:
        s = L.fmt_it(it)
        if s not in seen:
            seen.add(s)
            print('  ', s, flush=True)
