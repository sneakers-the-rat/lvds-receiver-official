"""t_ax33: R20 -> (69.5,2.9) rot90 move design (model).
Rips: SCL stub (2 F segs, via, 4 In2 segs), R20.2 feed segs A/B/D,
old R20 pads. Adds: +3V3D re-join seg C', new R20 pads, SCL web
(F A* pad1->via (70.95,2.85), via, B hop -> staircase vertex
(70.875,2.625)), +3V3D web (F A* pad2 -> U8 +3V3D pad (70.7,5.75)).
Gates everything; fragment counts before/after."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

BOXD = (55, 82, -10, 18)
pool = load_board_pool()
FB = {n: len(fragsets(pool, n, BOXD)) for n in ('I2C_SCL', '+3V3D')}
print('BEFORE:', FB, flush=True)
manifest = {'rips': [], 'news': [], 'move': ('R20', (69.5, 2.9), 90)}


def rip1(it, l=None):
    n = rip_items([it])
    manifest['rips'].append((it[0], it[1], l, tuple(it[2])))
    return n


# --- rips: SCL stub
stub = [
    ('seg', 'I2C_SCL', (69.675, 12.75, 69.625, 12.625, 0.1), 0.2),
    ('seg', 'I2C_SCL', (69.425, 12.75, 69.675, 12.75, 0.1), 0.2),
    ('via', 'I2C_SCL', (69.625, 12.625, 0.3), 0.2),
    ('seg', 'I2C_SCL', (69.625, 12.625, 65.0, 12.5, 0.1), 0.2),
    ('seg', 'I2C_SCL', (65.0, 12.5, 64.75, 12.0, 0.1), 0.2),
    ('seg', 'I2C_SCL', (64.75, 12.0, 65.25, 8.5, 0.1), 0.2),
    ('seg', 'I2C_SCL', (65.25, 8.5, 66.875, 6.75, 0.1), 0.2),
]
tot = 0
for it in stub:
    tot += rip1(it)
print(f'stub rip removals: {tot} (expect 2+3+4=9)', flush=True)
# old R20 pads out of the pool (they move with the footprint)
for net, cx in (('I2C_SCL', 69.425), ('+3V3D', 71.075)):
    pads = [it for it in pool[0] if it[0] == 'pad' and it[1] == net
            and abs(it[2][0] - cx) < 0.01 and abs(it[2][1] - 12.75) < 0.01]
    for p in pads:
        rip1(p)
        print(f'  old pad out: {L.fmt_it(p)}', flush=True)
# --- rips: R20.2 feed A/B/D + add re-join C'
feed = [
    ('seg', '+3V3D', (70.875, 12.625, 70.825, 12.75, 0.1), 0.25),
    ('seg', '+3V3D', (70.825, 12.75, 71.075, 12.75, 0.1), 0.25),
    ('seg', '+3V3D', (70.825, 12.75, 70.625, 12.375, 0.1), 0.25),
]
for it in feed:
    n = rip1(it)
    print(f'  feed rip {L.fmt_it(it)}: {n}', flush=True)
cj = ('seg', '+3V3D', (70.625, 12.375, 70.875, 12.625, 0.1), 0.25)
m = min(item_margin(0, cj, [o]) for o in pool[0] if o[1] != '+3V3D')
print(f're-join C\' gate: {m:+.3f}', flush=True)
pool[0].append(cj)
manifest['news'].append(('seg', '+3V3D', 0, tuple(cj[2])))
# --- new R20 pads (69.5,2.9) rot90: pad1 SCL (69.5,2.075), pad2 +3V3D
# (69.5,3.725); pad rect hw(x) 0.475 hh(y) 0.4
p1 = ('pad', 'I2C_SCL', (69.5, 2.075, 0.475, 0.4, 0.0), 0.2)
p2 = ('pad', '+3V3D', (69.5, 3.725, 0.475, 0.4, 0.0), 0.25)
pool[0].append(p1)
pool[0].append(p2)
manifest['news'].append(('pad', 'I2C_SCL', 0, (69.5, 2.075)))
manifest['news'].append(('pad', '+3V3D', 0, (69.5, 3.725)))

# --- SCL web: F A* pad1 -> via point, via, B hop
astar = make_astar((68.8, 71.6, 1.2, 3.6), 0.025)
J = astar('I2C_SCL', ((0,), 69.5, 2.075), (0, 70.95, 2.85), hw=0.10,
          layer_lock=[1, 0, 0])
print('SCL F A*:', 'FOUND' if J else 'NONE', flush=True)
if not J:
    raise SystemExit('SCL F NONE')
its = journey_items_dense(J, 'I2C_SCL', hw=0.10)
worst = (9.9, None)
for l in range(3):
    for it in its[l]:
        for o in pool[l]:
            if o[1] == 'I2C_SCL':
                continue
            mm = item_margin(l, it, [o])
            if mm < worst[0]:
                worst = (mm, o)
print(f'SCL F gate worst {worst[0]:+.3f} vs {L.fmt_it(worst[1])}',
      flush=True)
add_items(its)
manifest['news'] += [('seg', 'I2C_SCL', l, tuple(it[2]))
                     for l in range(3) for it in its[l]]
via = ('via', 'I2C_SCL', (70.95, 2.85, 0.25), 0.2)
for l in range(3):
    mm = min(item_margin(l, via, [o]) for o in pool[l]
             if o[1] != 'I2C_SCL')
    print(f'  SCL via margin L{l}: {mm:+.3f}', flush=True)
add_items({0: [via], 2: [via]})
pool[1].append(via)
manifest['news'].append(('via', 'I2C_SCL', (70.95, 2.85), 0.25))
hop = ('seg', 'I2C_SCL', (70.95, 2.85, 70.875, 2.625, 0.1), 0.2)
mm = min(item_margin(2, hop, [o]) for o in pool[2] if o[1] != 'I2C_SCL')
print(f'B hop gate: {mm:+.3f}', flush=True)
pool[2].append(hop)
manifest['news'].append(('seg', 'I2C_SCL', 2, tuple(hop[2])))

# --- +3V3D web: F A* pad2 -> U8 pad (70.7,5.75)
astar = make_astar((68.8, 71.4, 3.2, 6.2), 0.025)
J = astar('+3V3D', ((0,), 69.5, 3.725), (0, 70.7, 5.75), hw=0.10,
          layer_lock=[1, 0, 0])
print('+3V3D F A*:', 'FOUND' if J else 'NONE', flush=True)
if not J:
    raise SystemExit('+3V3D F NONE')
its = journey_items_dense(J, '+3V3D', hw=0.10)
worst = (9.9, None)
for l in range(3):
    for it in its[l]:
        for o in pool[l]:
            if o[1] == '+3V3D':
                continue
            mm = item_margin(l, it, [o])
            if mm < worst[0]:
                worst = (mm, o)
print(f'+3V3D F gate worst {worst[0]:+.3f} vs {L.fmt_it(worst[1])}',
      flush=True)
add_items(its)
manifest['news'] += [('seg', '+3V3D', l, tuple(it[2]))
                     for l in range(3) for it in its[l]]

FA = {n: len(fragsets(pool, n, BOXD)) for n in FB}
print('AFTER:', FA, flush=True)
with open('scratch/work/ax/manifest_ax33.json', 'w') as f:
    json.dump(manifest, f, indent=1, default=str)
print('manifest written', flush=True)
