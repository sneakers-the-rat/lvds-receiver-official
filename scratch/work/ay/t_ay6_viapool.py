import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for lay in range(3):
    hits = [it for it in pool[lay] if it[0] == 'via' and abs(it[2][0]-73.434) < 0.01 and abs(it[2][1]-17.685) < 0.01]
    print('layer', lay, 'GND via 73.434:', hits)
    hits2 = [it for it in pool[lay] if it[0] == 'via' and abs(it[2][0]-78.1) < 0.01 and abs(it[2][1]-17.5) < 0.01]
    print('layer', lay, 'PHY via 78.1:', hits2)
