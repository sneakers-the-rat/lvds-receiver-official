"""t_ax51: FULL southern R20 design.
Rips: SCL stub (7), +3V3D feed A/B/D (3), old R20 pads (2).
News: +3V3D re-join C'; R20 pads at (68.5,-1.75) rot0;
SCL F journey pad1 (67.675,-1.75) -> pocket via (69.35,1.4);
+3V3D ML journey pad2 (69.325,-1.75) -> B chain (73.15,1.25)
(southern loop). Gates all; fragments before/after; manifest out."""
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
BLK = ('via', 'BLOCKER', (72.85, -5.55, 0.5), 0.2)
for _l in range(3):
    pool[_l].append(BLK)
for _bx, _by in ((69.3, -3.0), (69.3, -5.0), (69.3, -7.0),
                 (69.3, -8.8)):
    _b = ('via', 'BLOCKER', (_bx, _by, 0.35), 0.2)
    for _l in range(3):
        pool[_l].append(_b)
FB = {n: len(fragsets(pool, n, BOXD))
      for n in ('I2C_SCL', '+3V3D', 'I2C_SDA')}
print('BEFORE:', FB, flush=True)
rips, news = [], []
for it in STUB + FEED:
    n = rip_items([it])
    rips.append((it[0], it[1], tuple(it[2]), n))
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


def run(net, start, goal, box, lock, label, hw=0.10):
    astar = make_astar(box, 0.025)
    J = astar(net, start, goal, hw=hw, layer_lock=lock)
    print(f'{label}:', 'FOUND' if J else 'NONE', flush=True)
    if not J:
        raise SystemExit(f'{label} NONE')
    its = journey_items_dense(J, net, hw=hw)
    worst = (9.9, None, None)
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < worst[0]:
                    worst = (m, it, o)
    print(f'   gate worst {worst[0]:+.3f} {L.fmt_it(worst[1])} vs '
          f'{L.fmt_it(worst[2])}', flush=True)
    add_items(its)
    seen_v = set()
    for l in range(3):
        for it in its[l]:
            if it[0] == 'via':
                if (it[2][0], it[2][1]) not in seen_v:
                    seen_v.add((it[2][0], it[2][1]))
                    news.append(('via', net, (it[2][0], it[2][1]),
                                 it[2][2]))
            else:
                news.append(('seg', net, l, tuple(it[2])))
    print(f'   vias: {sorted(seen_v)}', flush=True)
    return J


run('I2C_SCL', ((0,), 67.675, -1.75), (0, 69.35, 1.4),
    (64.0, 72.0, -4.5, 3.0), [1, 0, 0], 'SCL F')
run('+3V3D', ((0,), 69.325, -1.75), (2, 73.15, 1.25),
    (65.5, 75.5, -10.5, 4.5), None, '+3V3D loop')
FA = {n: len(fragsets(pool, n, BOXD)) for n in FB}
print('AFTER:', FA, flush=True)
with open('scratch/work/ax/manifest_ax67.json', 'w') as f:
    json.dump({'rips': rips, 'news': news,
               'move': ('R20', (68.5, -1.75), 0)}, f, indent=1,
              default=str)
print('manifest saved', flush=True)
