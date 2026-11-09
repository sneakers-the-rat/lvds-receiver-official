import sys
sys.path.insert(0, 'scratch/work/ax')
import t_ax0_pre as P
P.BOARD = 'hw/pdlvds_rx.exp242.kicad_pcb'
from t_ax0_pre import *  # noqa
pool = load_board_pool()
for name, box in (('island26', (66.99, 67.81, 0.46, 1.25)),
                  ('island29', (68.31, 72.19, -11.19, -7.0))):
    ok = []
    y = box[2]
    while y <= box[3]:
        x = box[0]
        while x <= box[1]:
            via = ('via', 'GND', (round(x, 3), round(y, 3), 0.25), 0.2)
            m = min(min(item_margin(l, via, [o]) for o in pool[l]
                        if o[1] != 'GND') for l in range(3))
            if m >= 0.0:
                ok.append((round(m, 3), round(x, 3), round(y, 3)))
            x += 0.05
        y += 0.05
    ok.sort(reverse=True)
    print(f'{name}: {len(ok)} legal via points; best {ok[:6]}',
          flush=True)
