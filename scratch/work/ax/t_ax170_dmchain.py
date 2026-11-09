import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for net in ('DM_PHY', 'ULPI_NXT', 'ULPI_DIR'):
    for l in range(3):
        its = [it for it in pool[l] if it[1] == net]
        print(f'{net} layer {l}: {len(its)} items', flush=True)
        for it in its:
            print('   ', L.fmt_it(it), flush=True)
