import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
STUB = [
    ('seg', 'I2C_SCL', (69.675, 12.75, 69.625, 12.625, 0.1), 0.2),
    ('seg', 'I2C_SCL', (69.425, 12.75, 69.675, 12.75, 0.1), 0.2),
    ('via', 'I2C_SCL', (69.625, 12.625, 0.3), 0.2),
    ('seg', 'I2C_SCL', (69.625, 12.625, 65.0, 12.5, 0.1), 0.2),
    ('seg', 'I2C_SCL', (65.0, 12.5, 64.75, 12.0, 0.1), 0.2),
    ('seg', 'I2C_SCL', (64.75, 12.0, 65.25, 8.5, 0.1), 0.2),
    ('seg', 'I2C_SCL', (65.25, 8.5, 66.875, 6.75, 0.1), 0.2),
]
FEED = [
    ('seg', '+3V3D', (70.875, 12.625, 70.825, 12.75, 0.1), 0.25),
    ('seg', '+3V3D', (70.825, 12.75, 71.075, 12.75, 0.1), 0.25),
    ('seg', '+3V3D', (70.825, 12.75, 70.625, 12.375, 0.1), 0.25),
]
pool = load_board_pool()
for it in STUB + FEED:
    rip_items([it])
for net, px in (('I2C_SCL', 69.425), ('+3V3D', 71.075)):
    for p in [it for it in pool[0] if it[0] == 'pad' and it[1] == net
              and abs(it[2][0] - px) < 0.01
              and abs(it[2][1] - 12.75) < 0.01]:
        rip_items([p])
pool[0].append(('seg', '+3V3D', (70.625, 12.375, 70.875, 12.625, 0.1),
                0.25))
pool[0].append(('pad', '+3V3D', (69.325, -1.75, 0.4, 0.475, 0.0),
                0.25))
# (a) In2 V1 -> staircase via
astar = make_astar((69.4, 73.2, -2.1, 3.6), 0.025)
J = astar('+3V3D', ((1,), 69.675, -1.65), (1, 72.875, 3.375), hw=0.10)
print('(a) In2 V1 -> staircase via:', 'FOUND' if J else 'NONE',
      flush=True)
if J:
    print('   vias:', J['vias'], flush=True)
# (b) In2 V1 -> (72.9,2.2), then B -> staircase via
astar = make_astar((69.4, 73.2, -2.1, 3.6), 0.025)
J = astar('+3V3D', ((1,), 69.675, -1.65), (1, 72.9, 2.2), hw=0.10)
print('(b) In2 V1 -> (72.9,2.2):', 'FOUND' if J else 'NONE', flush=True)
if J:
    print('   vias:', J['vias'], flush=True)
    astar = make_astar((72.5, 73.2, 1.8, 3.6), 0.025)
    J2 = astar('+3V3D', ((2,), 72.9, 2.2), (2, 72.875, 3.375), hw=0.10)
    print('    B (72.9,2.2) -> staircase via:',
          'FOUND' if J2 else 'NONE', flush=True)
