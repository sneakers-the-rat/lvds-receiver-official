import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool()
print('F items in (68.8,72.0,-2.8,-0.6):', flush=True)
for it in pool[0]:
    d = it[2]
    if 68.8 < d[0] < 72.0 and -2.8 < d[1] < -0.6:
        print('  ', L.fmt_it(it), flush=True)
others = [o for o in pool[0] if o[1] != '+3V3D']
for x in (69.5, 69.875, 70.2, 70.6):
    m, b = L.pt_margin(0, x, -1.75, '+3V3D', 0.10, others)
    print(f'F ({x},-1.75): {m:+.3f} binder {L.fmt_it(b)}', flush=True)
