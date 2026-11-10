import sys
sys.path.insert(0, 'scratch/work/ax'); sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *
import t_ai_lib as L
pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')
for it in pool[2]:
    if it[1] == 'PHY_1V8' and it[0] == 'seg':
        d = it[2]
        if 76.5 < min(d[0], d[2]) and max(d[0], d[2]) < 78.3 and 9.5 < min(d[1], d[3]) and max(d[1], d[3]) < 17.0:
            print('B:', L.fmt_it(it))
for it in pool[2]:
    if it[1] == 'PHY_1V8' and it[0] == 'via':
        d = it[2]
        if 76.5 < d[0] < 78.3 and 9.5 < d[1] < 17.0:
            print('B via:', L.fmt_it(it))
