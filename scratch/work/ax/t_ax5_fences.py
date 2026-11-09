"""t_ax5: ground truth of the window fence stack.
1) Raw segs of CAP_DATA/GND/CDR_LOL/CAP_CLK centred in
   (65.8,68.2,3.6,6.8), per layer (uncoalesced micro-segs, decimated).
2) Fine viafit scan for SCL via r0.25 in (66.6,68.6,4.2,6.4) step
   0.05; for the 8 best points print the binding item per layer."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

pool = load_board_pool()
BOX = (65.8, 68.2, 3.6, 6.8)
for net in ('CAP_DATA', 'GND', 'CDR_LOL', 'CAP_CLK'):
    for l in range(3):
        its = [it for it in pool[l] if it[1] == net and it[0] == 'seg'
               and BOX[0] < C(it)[0] < BOX[1] and BOX[2] < C(it)[1] < BOX[3]]
        if its:
            print(f'--- {net} L{l}: {len(its)} segs ---', flush=True)
            for it in its[::3]:
                print(f'  {L.fmt_it(it)}', flush=True)

print('=== fine viafit (66.6,68.6,4.2,6.4) step 0.05 ===', flush=True)
others = {l: [it for it in pool[l] if it[1] != 'I2C_SCL'] for l in range(3)}
res = []
y = 4.2
while y <= 6.4:
    x = 66.6
    while x <= 68.6:
        ms = [L.pt_margin(l, x, y, 'I2C_SCL', 0.25, others[l])
              for l in range(3)]
        m = min(v[0] for v in ms)
        res.append((m, round(x, 2), round(y, 2),
                    [(round(v[0], 3), v[1]) for v in ms]))
        x += 0.05
    y += 0.05
res.sort(reverse=True)
for m, x, y, per in res[:8]:
    print(f'({x},{y}) min {m:+.3f}', flush=True)
    for l, (mm, binder) in enumerate(per):
        print(f'   L{l} {mm:+.3f} binder: '
              f'{L.fmt_it(binder) if binder else None}', flush=True)
