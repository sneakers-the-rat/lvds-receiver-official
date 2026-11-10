import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
exec(open('scratch/work/ax/t_ax184_design214f.py').read().split('box =')[0]
     .split('pool = load_board_pool')[1].replace(
         "('hw/pdlvds_rx.exp250.kicad_pcb')", "('hw/pdlvds_rx.exp250.kicad_pcb')", 1))
