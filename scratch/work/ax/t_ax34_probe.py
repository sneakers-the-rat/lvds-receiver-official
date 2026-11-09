import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool()
stub = [
    ('seg', 'I2C_SCL', (69.675, 12.75, 69.625, 12.625, 0.1), 0.2),
    ('seg', 'I2C_SCL', (69.425, 12.75, 69.675, 12.75, 0.1), 0.2),
    ('via', 'I2C_SCL', (69.625, 12.625, 0.3), 0.2),
    ('seg', 'I2C_SCL', (69.625, 12.625, 65.0, 12.5, 0.1), 0.2),
    ('seg', 'I2C_SCL', (65.0, 12.5, 64.75, 12.0, 0.1), 0.2),
    ('seg', 'I2C_SCL', (64.75, 12.0, 65.25, 8.5, 0.1), 0.2),
    ('seg', 'I2C_SCL', (65.25, 8.5, 66.875, 6.75, 0.1), 0.2),
]
for it in stub:
    rip_items([it])
others = [o for o in pool[0] if o[1] != 'I2C_SCL']
for (x, y) in ((69.5, 2.075), (69.9, 2.4), (70.2, 2.62), (70.6, 2.8),
               (70.95, 2.85), (70.4, 2.3), (69.7, 2.2), (70.95, 2.6)):
    m, b = L.pt_margin(0, x, y, 'I2C_SCL', 0.10, others)
    print(f'F ({x},{y}): {m:+.3f} binder {L.fmt_it(b)}', flush=True)
print('F items in (69.3,71.3,1.8,3.4):', flush=True)
for it in pool[0]:
    d = it[2]
    if 69.3 < d[0] < 71.3 and 1.8 < d[1] < 3.4 and it[1] != 'I2C_SCL':
        print('  ', L.fmt_it(it), flush=True)
