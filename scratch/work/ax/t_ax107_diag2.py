import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
for lay, nm in ((1, 'In2'), (2, 'B')):
    print(f'== {nm} items in (67.5,72.5,11,16):', flush=True)
    seen = set()
    for it in pool[lay]:
        d = it[2]
        if 67.5 < d[0] < 72.5 and 11 < d[1] < 16:
            s = L.fmt_it(it)
            if s not in seen and len(s) < 120:
                seen.add(s)
                print('  ', s, flush=True)
