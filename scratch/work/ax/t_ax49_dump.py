import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool()
for lay, nm in ((1, 'In2'), (2, 'B')):
    print(f'== {nm} items in (69.0,73.5,-2.5,3.8):', flush=True)
    seen = set()
    for it in pool[lay]:
        d = it[2]
        if 69.0 < d[0] < 73.5 and -2.5 < d[1] < 3.8:
            s = L.fmt_it(it)
            if s not in seen:
                seen.add(s)
                print('  ', s, flush=True)
