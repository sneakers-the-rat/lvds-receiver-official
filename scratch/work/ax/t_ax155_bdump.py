import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for l in (2,):
    print(f'== layer {l} items (73.5,79.5,9,19.5):', flush=True)
    seen = set()
    for it in pool[l]:
        d = it[2]
        if 73.5 < d[0] < 79.5 and 9 < d[1] < 19.5:
            s = L.fmt_it(it)
            if s not in seen:
                seen.add(s)
                print('  ', s, flush=True)
