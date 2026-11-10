import sys
sys.path.insert(0, 'scratch/work/ax'); sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *
import t_ai_lib as L
pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')
for a, b in [((77.55, 10.35), (77.8, 16.2)), ((77.25, 10.75), (76.95, 11.05))]:
    try:
        ch = chain_segs(pool, 'PHY_1V8', 2, a, b)
        print(f'chain {a}->{b}: {len(ch)} segs')
        pts = [(round(it[2][0],3), round(it[2][1],3)) for it in ch]
        pts.append((round(ch[-1][2][2],3), round(ch[-1][2][3],3)))
        print('   ', pts)
    except SystemExit as e:
        print(f'chain {a}->{b} FAILED', e)
