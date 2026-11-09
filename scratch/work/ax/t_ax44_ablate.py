"""t_ax44: diagnostic ablation. Pool = southern R20 site state
(stub/feed ripped, re-join C', R20 pads at (68.5,-1.75) rot0).
A* +3V3D pad2 (69.325,-1.75) -> staircase via (72.875,3.375) ML,
with each candidate braid net's items in box (66.5,73.5,-3.5,2.0)
removed one at a time. Diagnostic only: identifies the binding
fence; any re-lay is designed explicitly afterwards."""
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
BOX = (66.5, 73.5, -3.5, 2.0)
CANDS = ['ULPI_DIR', 'ULPI_NXT', 'ULPI_STP', 'ULPI_D0', 'ULPI_D1',
         'ULPI_D2', 'ULPI_D3', 'I2C_SDA', 'HV_SHDN', 'ULPI_CLK']


def in_box(it):
    d = it[2]
    return BOX[0] <= d[0] <= BOX[1] and BOX[2] <= d[1] <= BOX[3]


def trial(ablate_net):
    pool = load_board_pool()
    for it in STUB + FEED:
        rip_items([it])
    for net, px in (('I2C_SCL', 69.425), ('+3V3D', 71.075)):
        for p in [it for it in pool[0] if it[0] == 'pad'
                  and it[1] == net and abs(it[2][0] - px) < 0.01
                  and abs(it[2][1] - 12.75) < 0.01]:
            rip_items([p])
    pool[0].append(('seg', '+3V3D',
                    (70.625, 12.375, 70.875, 12.625, 0.1), 0.25))
    pool[0].append(('pad', 'I2C_SCL', (67.675, -1.75, 0.4, 0.475, 0.0),
                    0.2))
    pool[0].append(('pad', '+3V3D', (69.325, -1.75, 0.4, 0.475, 0.0),
                    0.25))
    if ablate_net:
        for l in range(3):
            for it in list(pool[l]):
                if it[1] == ablate_net and in_box(it):
                    rip_items([it])
    astar = make_astar((66.0, 74.0, -3.0, 4.5), 0.025)
    J = astar('+3V3D', ((0,), 69.325, -1.75), (2, 72.875, 3.375),
              hw=0.10)
    return J


J = trial(None)
print('baseline (no ablation):', 'FOUND' if J else 'NONE', flush=True)
for net in CANDS:
    J = trial(net)
    print(f'ablate {net}:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        print('   vias:', J['vias'], flush=True)
