"""t_ax45: full southern-R20 design.
Pool: stub/feed rips, re-join C', R20 pads at (68.5,-1.75) rot0.
1) +3V3D journey with SDA braid-box items ablated (diagnostic pool)
   -> print runs, find crossing of x=69.875 on the non-F layer.
2) In the REAL pool: rip SDA B vertical segs in the crossing window,
   A* SDA's replacement on the other layer between the cut joints.
3) Add SCL F journey (t_ax37 design) + SDA swap + +3V3D journey;
   gate everything; fragment counts for SCL/+3V3D/SDA."""
import sys, json
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
BOXD = (55, 82, -12, 18)


def base_pool():
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
    return pool


# ---- step 1: ablated +3V3D journey
pool = base_pool()
for l in range(3):
    for it in list(pool[l]):
        if it[1] == 'I2C_SDA' and 66.5 <= it[2][0] <= 73.5 \
                and -3.5 <= it[2][1] <= 2.0:
            rip_items([it])
astar = make_astar((66.0, 74.0, -3.0, 4.5), 0.025)
J3 = astar('+3V3D', ((0,), 69.325, -1.75), (2, 72.875, 3.375), hw=0.10)
print('+3V3D journey (SDA ablated):', 'FOUND' if J3 else 'NONE',
      flush=True)
for r in J3['runs']:
    print('   run', r, flush=True)
print('   vias:', J3['vias'], flush=True)
# crossing of x=69.875 on non-F runs
for r in J3['runs']:
    lay, x1, y1, x2, y2 = r[0], r[1], r[2], r[3], r[4]
    if lay != 0 and (x1 - 69.875) * (x2 - 69.875) <= 0 and x1 != x2:
        t = (69.875 - x1) / (x2 - x1)
        print(f'   crossing x69.875 on L{lay} at y='
              f'{y1 + t * (y2 - y1):.3f}', flush=True)

# ---- SCL journey (real pool conditions)
pool = base_pool()
astar = make_astar((64.0, 72.0, -4.5, 3.0), 0.025)
JS = astar('I2C_SCL', ((0,), 67.675, -1.75), (0, 69.35, 1.4), hw=0.10)
print('SCL journey:', 'FOUND' if JS else 'NONE', flush=True)

# ---- step 2: SDA B vertical census in the south field
print('SDA items near x69.875, y -10..2:', flush=True)
for l in range(3):
    for it in pool[l]:
        if it[1] == 'I2C_SDA' and abs(it[2][0] - 69.875) < 0.3 \
                and -10.5 < it[2][1] < 2.5:
            print(f'   L{l} {L.fmt_it(it)}', flush=True)
with open('scratch/work/ax/journeys_ax45.json', 'w') as f:
    json.dump({'J3_runs': J3['runs'], 'J3_vias': J3['vias'],
               'JS_runs': JS['runs'], 'JS_vias': JS['vias']}, f,
              indent=1)
print('journeys saved', flush=True)
