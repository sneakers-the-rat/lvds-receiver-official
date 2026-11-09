import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
FULL = (-50.0, 200.0, -100.0, 100.0)
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for net in ('PHY_1V8A', 'XO'):
    fs = fragments(net, FULL)
    print(net, 'fragments:', len(fs), [len(f['items']) for f in fs],
          flush=True)
