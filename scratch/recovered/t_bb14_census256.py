"""t_bb14: census for the exp256 fix: B items x[68,76.5] y[12,21]
(ride west route), XO F items in the staircase box, DIR/CAP B west."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp255.kicad_pcb')
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
print('--- B items x[68,76.5] y[12,21] ---')
rows = []
for it in pool[2]:
    c = C(it)
    if 68.0 <= c[0] <= 76.5 and 12.0 <= c[1] <= 21.0:
        rows.append((round(c[1], 2), round(c[0], 2), it))
for _, _, it in sorted(rows):
    print('  B  ', it[1].ljust(10), L.fmt_item(it))
print('--- XO F items x[75.8,77.0] y[9.4,11.8] ---')
for it in pool[0]:
    if it[1] != 'XO':
        continue
    c = C(it)
    if 75.8 <= c[0] <= 77.0 and 9.4 <= c[1] <= 11.8:
        print('  F   XO', L.fmt_item(it))
print('--- CAP_CLK B items x[68,76] (y range check) ---')
ys = []
for it in pool[2]:
    if it[1] == 'CAP_CLK':
        c = C(it)
        if 68.0 <= c[0] <= 76.0:
            ys.append((round(c[0], 2), round(c[1], 2)))
print('  CAP_CLK B centres x[68,76]:', sorted(ys)[:40])
print('  count:', len(ys))
