"""t_ax11: SCL bridge design v3 at W5=(67.5,5.8).
Sequence: SCL via + In2 approach seg placed first (obstacles), then
M1 GND In2 staircase re-lay, M2 CDR_LOL B band re-lay E, M3 +3V3D F
corner re-lay N, M4 B ride W4->pocket via (69.35,1.4). Gates every
new item vs the final pool; fragment recount; manifest to JSON."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

W = (67.5, 5.8)
BOXD = (55, 82, -10, 18)


def gate_journey(J, net, hw, tag):
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
    print(f'{tag}: worst gate {worst[0]:+.3f} '
          f'{L.fmt_it(worst[1])} vs {L.fmt_it(worst[2])}', flush=True)
    return its, worst[0]


def emit(its):
    add_items(its)


pool = load_board_pool()
FB = {n: len(fragsets(pool, n, BOXD))
      for n in ('I2C_SCL', 'GND', 'CDR_LOL', '+3V3D')}
print('BEFORE:', FB, flush=True)
manifest = {'W': W, 'rips': [], 'news': []}

# 0. SCL via + approach
via = ('via', 'I2C_SCL', (W[0], W[1], 0.25), 0.2)
seg = ('seg', 'I2C_SCL', (66.875, 6.75, W[0], W[1], 0.10), 0.2)
add_items({0: [via], 2: [via]})
pool[1].append(via)
pool[1].append(seg)
manifest['news'].append(('via', 'I2C_SCL', W, 0.25))
manifest['news'].append(('seg', 'I2C_SCL', 1, (66.875, 6.75, W[0], W[1],
                                               0.10)))
mm0 = min(item_margin(1, seg, [o]) for o in pool[1]
          if o[1] != 'I2C_SCL')
print(f'approach margin now: {mm0:+.3f}', flush=True)

# M1 GND In2
rip = chain_segs(pool, 'GND', 1, (66.375, 6.125), (67.375, 4.125))
n = rip_items(rip)
assert n == len(rip), (n, len(rip))
manifest['rips'] += [('seg', 'GND', 1, tuple(it[2])) for it in rip]
astar = make_astar((65.4, 68.2, 3.4, 7.0), 0.025)
J = astar('GND', ((1,), 66.375, 6.125), (1, 67.375, 4.125), hw=0.125)
print('M1 A*:', 'FOUND' if J else 'NONE', flush=True)
if not J:
    raise SystemExit('M1 NONE')
its, w1 = gate_journey(J, 'GND', 0.125, 'M1')
emit(its)
manifest['news'] += [('seg', 'GND', l, tuple(it[2]))
                     for l in range(3) for it in its[l]]

# M2 CDR_LOL B
rip = chain_segs(pool, 'CDR_LOL', 2, (67.625, 6.625), (68.375, 4.125))
n = rip_items(rip)
assert n == len(rip), (n, len(rip))
manifest['rips'] += [('seg', 'CDR_LOL', 2, tuple(it[2])) for it in rip]
astar = make_astar((66.2, 70.6, 3.0, 8.0), 0.025)
J = astar('CDR_LOL', ((2,), 67.625, 6.625), (2, 68.375, 4.125), hw=0.125,
          layer_lock=[0, 0, 1])
print('M2 A*:', 'FOUND' if J else 'NONE', flush=True)
if not J:
    raise SystemExit('M2 NONE')
its, w2 = gate_journey(J, 'CDR_LOL', 0.125, 'M2')
emit(its)
manifest['news'] += [('seg', 'CDR_LOL', l, tuple(it[2]))
                     for l in range(3) for it in its[l]]

# M3 +3V3D F corner (v2: whole corner from the feed point (67.55,7.25)
# at hw0.30; the original corner is mixed w0.2 jog + w0.6 lower segs,
# and the old jog point (67.375,6.625) is impassable at hw0.30 in
# U8's GND pad shadow)
rip = chain_segs(pool, '+3V3D', 0, (67.55, 7.25), (68.625, 6.125))
n = rip_items(rip)
assert n == len(rip), (n, len(rip))
manifest['rips'] += [('seg', '+3V3D', 0, tuple(it[2])) for it in rip]
astar = make_astar((66.6, 69.4, 5.4, 7.4), 0.025)
J = astar('+3V3D', ((0,), 67.55, 7.25), (0, 68.625, 6.125), hw=0.30,
          layer_lock=[1, 0, 0])
print('M3 A*:', 'FOUND' if J else 'NONE', flush=True)
if not J:
    raise SystemExit('M3 NONE')
its, w3 = gate_journey(J, '+3V3D', 0.30, 'M3')
emit(its)
manifest['news'] += [('seg', '+3V3D', l, tuple(it[2]))
                     for l in range(3) for it in its[l]]

# M4 B ride (v3: southern loop — +3V3A's B vertical x68.625 walls
# y4.875..16.625 and the LOL/+3V3A-via pinch seals its bottom; the
# pocket via's B island connects around the south below PG's dive)
astar = make_astar((65.5, 72.5, -2.6, 7.5), 0.025)
J = astar('I2C_SCL', ((2,), W[0], W[1]), (2, 69.35, 1.4), hw=0.10,
          layer_lock=[0, 0, 1])
print('M4 A*:', 'FOUND' if J else 'NONE', flush=True)
if not J:
    raise SystemExit('M4 NONE')
its, w4 = gate_journey(J, 'I2C_SCL', 0.10, 'M4')
emit(its)
manifest['news'] += [('seg', 'I2C_SCL', l, tuple(it[2]))
                     for l in range(3) for it in its[l]]

# final gates: via + approach vs everything
for l in range(3):
    mm = item_margin(l, via, [o for o in pool[l] if o[1] != 'I2C_SCL'])
    print(f'via margin L{l} final: {mm:+.3f}', flush=True)
mm = item_margin(1, seg, [o for o in pool[1] if o[1] != 'I2C_SCL'])
print(f'approach margin final: {mm:+.3f}', flush=True)

FA = {n: len(fragsets(pool, n, BOXD)) for n in FB}
print('AFTER:', FA, flush=True)
worst_all = min(w1, w2, w3, w4)
print(f'WORST journey gate: {worst_all:+.3f}', flush=True)
with open('scratch/work/ax/manifest_ax11.json', 'w') as f:
    json.dump(manifest, f, indent=1, default=str)
print('manifest written:', len(manifest['rips']), 'rips,',
      len(manifest['news']), 'news', flush=True)
