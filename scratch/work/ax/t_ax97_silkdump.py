import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
seen = set()
for it in pool[0]:
    d = it[2]
    if 74.5 < d[0] < 78.5 and 33.5 < d[1] < 37.5:
        s = L.fmt_it(it)
        if s not in seen:
            seen.add(s)
            print('  ', s, flush=True)
