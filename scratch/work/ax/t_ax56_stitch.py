import sys
sys.path.insert(0, 'scratch/work/ax')
import t_ax0_pre as P
P.BOARD = 'hw/pdlvds_rx.exp242.kicad_pcb'
from t_ax0_pre import *  # noqa
pool = load_board_pool()
for (vx, vy) in ((67.4, 0.85), (68.65, -8.3), (70.6, -8.3),
                 (67.2, 0.9), (71.5, -10.5)):
    via = ('via', 'GND', (vx, vy, 0.25), 0.2)
    ms = []
    for l in range(3):
        m, b = 9.9, None
        for o in pool[l]:
            if o[1] == 'GND':
                continue
            mm = item_margin(l, via, [o])
            if mm < m:
                m, b = mm, o
        ms.append((m, b))
    print(f'GND via ({vx},{vy}): ' +
          ' '.join(f'L{l} {m:+.3f}' for l, (m, _) in enumerate(ms)) +
          f'  worst binder {L.fmt_it(min(ms, key=lambda t: t[0])[1])}',
          flush=True)
