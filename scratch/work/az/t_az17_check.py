import sys
sys.path.insert(0, 'scratch/work/ax'); sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *
import t_ai_lib as L
pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')
a = b = None
for it in pool[2]:
    if it[1] == 'PHY_1V8A' and it[0] == 'seg' and abs(it[2][0]-75.737) < 0.01:
        a = it
    if it[1] == '+3V3A' and it[0] == 'seg' and abs(it[2][2]-75.625) < 0.01 and abs(it[2][3]-10.975) < 0.01:
        b = it
print('A:', L.fmt_it(a) if a else None)
print('B:', L.fmt_it(b) if b else None)
if a and b:
    print('item_margin A vs B:', item_margin(2, a, [b]))
    print('item_margin B vs A:', item_margin(2, b, [a]))
