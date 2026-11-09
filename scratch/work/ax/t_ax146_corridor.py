import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for l in (1, 2):
    print(f'== layer {"In2" if l == 1 else "B"} items (73.5,79,2,14):',
          flush=True)
    seen = set()
    for it in pool[l]:
        d = it[2]
        if 73.5 < d[0] < 79 and 2 < d[1] < 14:
            s = L.fmt_it(it)
            if s not in seen:
                seen.add(s)
                print('  ', s, flush=True)
