import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool()
for it in pool[0]:
    if it[1] != '+3V3D' or it[0] != 'seg':
        continue
    d = it[2]
    if 66.0 < d[0] < 69.5 and 5.5 < d[1] < 7.6:
        print(L.fmt_it(it), flush=True)
