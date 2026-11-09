"""t_ax10: fine via scan (67.4,67.65,5.5,5.9) step 0.025.
For each point: per-layer margins + binders (pre-move pool)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

pool = load_board_pool()
others = {l: [o for o in pool[l] if o[1] != 'I2C_SCL'] for l in range(3)}
res = []
y = 5.5
while y <= 5.901:
    x = 67.4
    while x <= 67.651:
        per = [L.pt_margin(l, x, y, 'I2C_SCL', 0.25, others[l])
               for l in range(3)]
        res.append((min(v[0] for v in per), round(x, 3), round(y, 3),
                    per))
        x += 0.025
    y += 0.025
res.sort(reverse=True)
for m, x, y, per in res[:10]:
    print(f'({x},{y}) min {m:+.3f}: ' +
          ' '.join(f'L{l} {v[0]:+.3f}' for l, v in enumerate(per)),
          flush=True)
    for l, v in enumerate(per):
        if v[0] < 0.05:
            print(f'    L{l} binder: {L.fmt_it(v[1])}', flush=True)
