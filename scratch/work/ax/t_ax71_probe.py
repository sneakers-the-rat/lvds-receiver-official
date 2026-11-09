import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool()
others = [o for o in pool[0] if o[1] != 'I2C_SCL']
for (x, y) in ((66.9, -1.0), (66.5, -0.4), (66.3, 0.2), (66.25, 0.8),
               (66.3, 1.3), (66.8, 1.5), (66.6, 0.9), (66.45, 0.5)):
    m, b = L.pt_margin(0, x, y, 'I2C_SCL', 0.10, others)
    print(f'F ({x},{y}): {m:+.3f} binder {L.fmt_it(b)}', flush=True)
print('F items in (65.8,67.2,-1.6,1.6):', flush=True)
for it in pool[0]:
    d = it[2]
    if 65.8 < d[0] < 67.2 and -1.6 < d[1] < 1.6 and it[1] != 'I2C_SCL':
        print('  ', L.fmt_it(it), flush=True)
