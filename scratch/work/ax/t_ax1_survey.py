"""t_ax1: exp241 corridor survey for the I2C_SCL bridge.
SCL fragments + terms; every item (any net) centred in the corridor
box (63,71,-1,8) per layer; CDR_LOL and GND fragment structure."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

pool = load_board_pool()
print(f'pool sizes: {[len(pool[l]) for l in range(3)]}', flush=True)

fr = fragments('I2C_SCL', (55, 82, -10, 18))
print(f'SCL fragments: {len(fr)}', flush=True)
for i, f in enumerate(fr):
    print(f'--- SCL fragment {i}: {len(f["items"])} items; terms:', flush=True)
    for (l, p) in f['terms']:
        print(f'    term L{l} ({p[0]:.3f},{p[1]:.3f})', flush=True)
    for (l, it) in f['items']:
        if it[0] == 'pad':
            print(f'    L{l} {L.fmt_it(it)}', flush=True)

BOX = (63.0, 71.0, -1.0, 8.0)
for l in range(3):
    print(f'=== layer {l} items centred in {BOX} ===', flush=True)
    rows = []
    for it in pool[l]:
        cx, cy = C(it)
        if BOX[0] < cx < BOX[1] and BOX[2] < cy < BOX[3]:
            rows.append((it[1], L.fmt_it(it)))
    for net, s in sorted(rows):
        print(f'  {s}', flush=True)

for net in ('CDR_LOL', 'GND'):
    fr = fragments(net, (60, 74, -2, 10))
    print(f'{net}: {len(fr)} fragments in (60,74,-2,10)', flush=True)
    for i, f in enumerate(fr):
        near = [(l, it) for (l, it) in f['items']
                if BOX[0] - 1 < C(it)[0] < BOX[1] + 1
                and BOX[2] - 1 < C(it)[1] < BOX[3] + 1]
        if near:
            print(f'  frag {i} ({len(f["items"])} items, {len(near)} near box):',
                  flush=True)
            for (l, it) in near:
                print(f'    L{l} {L.fmt_it(it)}', flush=True)
