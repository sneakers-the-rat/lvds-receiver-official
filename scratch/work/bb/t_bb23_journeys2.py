"""t_bb23: per-layer journey tips/vias for XO, RBIAS, CAP_DATA,
CDR_DATN, CAP_CLK in the south-west quadrant (x<78, y>14)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp254.kicad_pcb')
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
for net in ('XO', 'RBIAS', 'CAP_DATA', 'CDR_DATN', 'CAP_CLK'):
    for l in range(3):
        vias, deg = [], {}
        for it in pool[l]:
            if it[1] != net:
                continue
            if it[0] == 'via':
                vias.append((round(it[2][0], 2), round(it[2][1], 2)))
            elif it[0] == 'seg':
                d = it[2]
                for p in ((round(d[0], 2), round(d[1], 2)),
                          (round(d[2], 2), round(d[3], 2))):
                    deg[p] = deg.get(p, 0) + 1
        tips = sorted(p for p, n in deg.items() if n == 1
                      and p[0] < 78 and p[1] > 14)
        vv = sorted(v for v in vias if v[0] < 78 and v[1] > 14)
        if tips or vv:
            print(f'{net} {LAYN[l]}: vias {vv} tips {tips}')
