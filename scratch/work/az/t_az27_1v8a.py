import sys
sys.path.insert(0, 'scratch/work/ax'); sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *
import t_ai_lib as L
pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')
pts = set()
for it in pool[2]:
    if it[1] == 'PHY_1V8A' and it[0] == 'seg':
        d = it[2]
        if 69 < min(d[0], d[2]) and max(d[0], d[2]) < 76.5 and 9 < min(d[1], d[3]) and max(d[1], d[3]) < 20:
            pts.add((round(d[0], 2), round(d[1], 2)))
            pts.add((round(d[2], 2), round(d[3], 2)))
    if it[1] == 'PHY_1V8A' and it[0] == 'via':
        d = it[2]
        if 69 < d[0] < 76.5 and 9 < d[1] < 20:
            print('1V8A B via:', L.fmt_it(it))
import collections
bands = collections.defaultdict(list)
for (x, y) in pts:
    bands[round(y)].append(x)
for y in sorted(bands):
    xs = bands[y]
    print(f'y~{y}: x {min(xs)}..{max(xs)} n={len(xs)}')
