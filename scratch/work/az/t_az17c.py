import sys
sys.path.insert(0, 'scratch/work/ax'); sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *
import t_ai_lib as L
pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')
for l in range(3):
    for it in pool[l]:
        if it[1] == '+3V3A' and it[0] == 'seg':
            d = it[2]
            if (74.5 < d[0] < 78 and 9.5 < d[1] < 12.5) or (74.5 < d[2] < 78 and 9.5 < d[3] < 12.5):
                print(f'L{l}:', L.fmt_it(it))
