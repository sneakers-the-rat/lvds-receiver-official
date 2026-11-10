import sys
sys.path.insert(0, 'scratch/work/ax'); sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *
import t_ai_lib as L
pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')
for l in range(3):
    for it in pool[l]:
        if it[1] != 'PHY_1V8':
            continue
        if it[0] == 'seg':
            d = it[2]
            for (px, py) in [(77.25, 10.75), (77.55, 10.35), (77.25, 10.7375)]:
                if (abs(d[0]-px) < 0.02 and abs(d[1]-py) < 0.02) or (abs(d[2]-px) < 0.02 and abs(d[3]-py) < 0.02):
                    print(f'L{l}:', L.fmt_it(it))
        elif it[0] == 'via':
            d = it[2]
            if abs(d[0]-77.25) < 0.02 and abs(d[1]-10.75) < 0.02:
                print(f'L{l} via:', L.fmt_it(it))
