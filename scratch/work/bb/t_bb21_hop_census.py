"""t_bb21: census for hop v10: F+In2 x[71.5,74.5] y[15.5,18.5]
(N2 candidate (72.5,16.6)); In2 x[70,76] y[16,21] (hop path);
B x[71.5,76] y[22.4,23.6] (south leg)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp254.kicad_pcb')
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
for layer, box, tag in ((0, (71.5, 74.5, 15.5, 18.5), 'F N2 box'),
                        (1, (71.5, 74.5, 15.5, 18.5), 'In2 N2 box'),
                        (1, (70.0, 76.0, 16.0, 21.0), 'In2 hop box'),
                        (2, (71.5, 76.0, 22.4, 23.6), 'B south leg')):
    print(f'--- {tag} ---')
    rows = []
    for it in pool[layer]:
        c = C(it)
        if box[0] <= c[0] <= box[1] and box[2] <= c[1] <= box[3]:
            rows.append((round(c[1], 2), round(c[0], 2), it))
    for _, _, it in sorted(rows):
        print('  ', LAYN[layer], it[1].ljust(10), L.fmt_it(it))
    print(f'   ({len(rows)} items)')
