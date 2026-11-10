"""t_bb20: B-layer journey extents for XI, CAP_DATA, DP_PHY,
ULPI_DIR, ULPI_NXT south of y16: all vias + seg endpoint ranges."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp254.kicad_pcb')
for net in ('XI', 'CAP_DATA', 'DP_PHY', 'ULPI_DIR', 'ULPI_NXT'):
    vias, ends = [], set()
    for it in pool[2]:
        if it[1] != net:
            continue
        if it[0] == 'via':
            vias.append((round(it[2][0], 2), round(it[2][1], 2), it[2][2]))
        elif it[0] == 'seg':
            d = it[2]
            ends.add((round(d[0], 2), round(d[1], 2)))
            ends.add((round(d[2], 2), round(d[3], 2)))
    deg = {}
    for it in pool[2]:
        if it[1] != net or it[0] != 'seg':
            continue
        d = it[2]
        for p in ((round(d[0], 2), round(d[1], 2)), (round(d[2], 2), round(d[3], 2))):
            deg[p] = deg.get(p, 0) + 1
    tips = sorted(p for p, n in deg.items() if n == 1)
    print(f'{net}: B vias {vias}')
    print(f'   B seg endpoints with degree 1 (tips): {tips}')
