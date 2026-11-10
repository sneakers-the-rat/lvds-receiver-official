import sys
sys.path.insert(0, 'scratch/work/ax'); sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *
import t_ai_lib as L
pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')
a = None
for it in pool[2]:
    if it[1] == 'PHY_1V8A' and it[0] == 'seg' and abs(it[2][0]-75.737) < 0.01:
        a = it
for it in pool[2]:
    if it[1] == '+3V3A' and it[0] == 'seg':
        d = it[2]
        if min(d[0], d[2]) < 76.9 and max(d[0], d[2]) > 75.5 and min(d[1], d[3]) > 10.5 and max(d[1], d[3]) < 12.2:
            print('cand:', L.fmt_it(it), 'margin vs A:', item_margin(2, it, [a]) if a else '-')
