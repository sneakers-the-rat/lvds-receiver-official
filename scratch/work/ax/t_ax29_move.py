"""t_ax29: R20 -> (80,9) move design probes.
- stub fragment exact items (to rip)
- R20.2 old feed segs incident to old pad (71.075,12.75)
- viafit at SCL via cand (78.62,8.45) and +3V3D via cand (81.3,8.9)
- SCL In2 items in (78,84,6,12); +3V3D In2 vertical span near x81.475
- micro A*: SCL F pad1 (79.175,9.0)->via; +3V3D F pad2 (80.825,9.0)->via
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

pool = load_board_pool()
fr = fragments('I2C_SCL', (40, 100, -30, 50))
for f in fr:
    its = [it for (l, it) in f['items']]
    if any(it[0] == 'via' and abs(it[2][0] - 69.625) < 0.01
           and abs(it[2][1] - 12.625) < 0.01 for it in its):
        print('STUB fragment items:', flush=True)
        seen = set()
        for (l, it) in f['items']:
            if it not in seen:
                seen.add(it)
                print(f'   L{l} {L.fmt_it(it)}', flush=True)
print('+3V3D F items incident to (71.075,12.75) pad:', flush=True)
for it in pool[0]:
    if it[1] != '+3V3D' or it[0] != 'seg':
        continue
    d = it[2]
    if (abs(d[0] - 71.075) < 0.6 and abs(d[1] - 12.75) < 0.6) or \
       (abs(d[2] - 71.075) < 0.6 and abs(d[3] - 12.75) < 0.6):
        print('  ', L.fmt_it(it), flush=True)
print('SCL In2 items in (78,84,6,12):', flush=True)
for it in pool[1]:
    if it[1] != 'I2C_SCL':
        continue
    d = it[2]
    if 77.5 < d[0] < 84 and 6 < d[1] < 12:
        print('  ', L.fmt_it(it), flush=True)
print('+3V3D In2 items with x in (81.2,81.8):', flush=True)
ys = []
for it in pool[1]:
    if it[1] != '+3V3D':
        continue
    d = it[2]
    if 81.2 < d[0] < 81.8:
        ys.append((round(d[1], 2), L.fmt_it(it)))
for (y, s) in sorted(ys)[:6]:
    print('  ', s, flush=True)
print('   ... total', len(ys), flush=True)

for (net, vx, vy) in (('I2C_SCL', 78.62, 8.45), ('+3V3D', 81.3, 8.9)):
    print(f'via cand {net} ({vx},{vy}):', flush=True)
    for l in range(3):
        others = [o for o in pool[l] if o[1] != net]
        m, bnd = L.pt_margin(l, vx, vy, net, 0.25, others)
        print(f'   L{l}: {m:+.3f} binder {L.fmt_it(bnd)}', flush=True)
