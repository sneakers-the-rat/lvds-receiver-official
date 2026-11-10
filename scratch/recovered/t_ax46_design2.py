"""t_ax46: southern R20 full design v2 (SDA untouched).
Pool: stub/feed rips, re-join C', R20 pads at (68.5,-1.75).
SCL: F journey pad1 -> pocket via (69.35,1.4).
+3V3D: F hop pad2 -> V1 (69.675,-1.65); In2 A* V1 -> V2 (70.6,-0.9);
B A* V2 -> staircase via (72.875,3.375); vias V1 (F/In2), V2 (In2/B).
Gate all journeys + vias; fragment counts SCL/+3V3D/SDA before/after;
save the design manifest."""
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
pool = load_board_pool()
FB = {n: len(fragsets(pool, n, BOXD))
      for n in ('I2C_SCL', '+3V3D', 'I2C_SDA')}
print('BEFORE:', FB, flush=True)
news = []
for it in STUB + FEED:
    rip_items([it])
for net, px in (('I2C_SCL', 69.425), ('+3V3D', 71.075)):
    for p in [it for it in pool[0] if it[0] == 'pad' and it[1] == net
              and abs(it[2][0] - px) < 0.01
              and abs(it[2][1] - 12.75) < 0.01]:
        rip_items([p])
cj = ('seg', '+3V3D', (70.625, 12.375, 70.875, 12.625, 0.1), 0.25)
pool[0].append(cj)
news.append(('seg', '+3V3D', 0, tuple(cj[2])))
pool[0].append(('pad', 'I2C_SCL', (67.675, -1.75, 0.4, 0.475, 0.0),
                0.2))
pool[0].append(('pad', '+3V3D', (69.325, -1.75, 0.4, 0.475, 0.0),
                0.25))


def gate_new(its, net):
    worst = (9.9, None, None)
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < worst[0]:
                    worst = (m, it, o)
    return worst


def run(net, start, goal, box, lock, label):
    astar = make_astar(box, 0.025)
    J = astar(net, start, goal, hw=0.10, layer_lock=lock)
    print(f'{label}:', 'FOUND' if J else 'NONE', flush=True)
    if not J:
        raise SystemExit(f'{label} NONE')
    its = journey_items_dense(J, net, hw=0.10)
    w = gate_new(its, net)
    print(f'   gate worst {w[0]:+.3f} {L.fmt_it(w[1])} vs '
          f'{L.fmt_it(w[2])}', flush=True)
    add_items(its)
    for l in range(3):
        for it in its[l]:
            news.append(('seg', net, l, tuple(it[2])))
    return J


# SCL F journey
run('I2C_SCL', ((0,), 67.675, -1.75), (0, 69.35, 1.4),
    (64.0, 72.0, -4.5, 3.0), [1, 0, 0], 'SCL F')
# +3V3D seg1: F hop to V1
run('+3V3D', ((0,), 69.325, -1.75), (0, 69.675, -1.65),
    (68.9, 70.1, -2.2, -1.2), [1, 0, 0], '+3V3D F hop')
# +3V3D seg2: In2 V1 -> V2
run('+3V3D', ((1,), 69.675, -1.65), (1, 70.6, -0.9),
    (69.3, 71.0, -2.1, -0.4), [0, 1, 0], '+3V3D In2')
# +3V3D seg3: B V2 -> staircase via
run('+3V3D', ((2,), 70.6, -0.9), (2, 72.875, 3.375),
    (70.2, 73.2, -1.3, 3.6), [0, 0, 1], '+3V3D B')
# vias V1, V2 (r0.25)
for (vx, vy) in ((69.675, -1.65), (70.6, -0.9)):
    via = ('via', '+3V3D', (vx, vy, 0.25), 0.25)
    for l in range(3):
        mm = min(item_margin(l, via, [o]) for o in pool[l]
                 if o[1] != '+3V3D')
        print(f'  via ({vx},{vy}) L{l} margin {mm:+.3f}', flush=True)
    for l in range(3):
        pool[l].append(via)
    news.append(('via', '+3V3D', (vx, vy), 0.25))
FA = {n: len(fragsets(pool, n, BOXD)) for n in FB}
print('AFTER:', FA, flush=True)
with open('scratch/work/ax/manifest_ax46.json', 'w') as f:
    json.dump({'news': news}, f, indent=1, default=str)
print('manifest saved', flush=True)
