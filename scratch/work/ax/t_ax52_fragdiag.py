import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
BOXD = (55, 82, -12, 18)
pool = load_board_pool()
print('BEFORE +3V3D fragments:', flush=True)
for i, f in enumerate(fragsets(pool, '+3V3D', BOXD)):
    ts = sorted(set((l, tuple(p)) for (l, p) in f['terms']))
    print(f'  frag{i}: {len(f["items"])} items, terms {ts[:6]}',
          flush=True)
man = json.load(open('scratch/work/ax/manifest_ax51.json'))
for (kind, net, tup, n) in man['rips']:
    pass
# replay rips by geometry (same lists as t_ax51)
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
for it in STUB + FEED:
    rip_items([it])
for net, px in (('I2C_SCL', 69.425), ('+3V3D', 71.075)):
    for p in [it for it in pool[0] if it[0] == 'pad' and it[1] == net
              and abs(it[2][0] - px) < 0.01
              and abs(it[2][1] - 12.75) < 0.01]:
        rip_items([p])
for e in man['news']:
    if e[0] == 'seg':
        _, net, l, tup = e
        pool[l].append(('seg', net, tuple(tup), 0.25 if net == '+3V3D'
                        else 0.2))
    elif e[0] == 'via':
        _, net, (vx, vy), vr = e
        for l in range(3):
            pool[l].append(('via', net, (vx, vy, vr),
                            0.25 if net == '+3V3D' else 0.2))
    elif e[0] == 'pad':
        pass
pool[0].append(('pad', 'I2C_SCL', (67.675, -1.75, 0.4, 0.475, 0.0),
                0.2))
pool[0].append(('pad', '+3V3D', (69.325, -1.75, 0.4, 0.475, 0.0),
                0.25))
print('AFTER +3V3D fragments:', flush=True)
for i, f in enumerate(fragsets(pool, '+3V3D', BOXD)):
    ts = sorted(set((l, tuple(p)) for (l, p) in f['terms']))
    print(f'  frag{i}: {len(f["items"])} items, terms {ts[:8]}',
          flush=True)
print('frag4 item detail:', flush=True)
for f in fragsets(pool, '+3V3D', BOXD):
    if len(f['items']) == 1:
        print('  ', f['items'], flush=True)
