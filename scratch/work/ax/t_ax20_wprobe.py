import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool()
others = [o for o in pool[2] if o[1] != 'I2C_SCL']
for (x, y) in ((66.5, 3.25), (66.3, 3.6), (66.6, 2.9), (67.0, 3.3),
               (66.2, 2.6), (66.8, 2.2), (67.3, 1.6), (68.0, 1.75)):
    m, b = L.pt_margin(2, x, y, 'I2C_SCL', 0.10, others)
    print(f'B ({x},{y}): {m:+.3f} binder {L.fmt_it(b)}', flush=True)
