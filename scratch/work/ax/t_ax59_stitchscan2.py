import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp242.kicad_pcb')
hits = [it for l in range(3) for it in pool[l]
        if it[0] == 'via' and abs(it[2][0] - 69.225) < 0.01
        and abs(it[2][1] + 9.075) < 0.01]
print('pool sanity, loop via present:', len(hits) > 0, flush=True)
for name, box in (('island26', (66.99, 67.81, 0.46, 1.25)),
                  ('island29', (68.31, 72.19, -11.19, -7.0))):
    local = {l: [o for o in pool[l] if o[1] != 'GND'
                 and box[0] - 2.5 < o[2][0] < box[1] + 2.5
                 and box[2] - 2.5 < o[2][1] < box[3] + 2.5]
             for l in range(3)}
    ok = []
    y = box[2]
    while y <= box[3]:
        x = box[0]
        while x <= box[1]:
            via = ('via', 'GND', (round(x, 3), round(y, 3), 0.25), 0.2)
            m = min(min(item_margin(l, via, [o]) for o in local[l])
                    for l in range(3))
            if m >= 0.0:
                ok.append((round(m, 3), round(x, 3), round(y, 3)))
            x += 0.1
        y += 0.1
    ok.sort(reverse=True)
    print(f'{name}: {len(ok)} legal via points; best {ok[:6]}',
          flush=True)
