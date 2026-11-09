import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for l in range(3):
    its = [it for it in pool[l] if it[1] == 'PHY_1V8']
    print(f'PHY_1V8 layer {l}: {len(its)} items', flush=True)
    for it in its:
        print('   ', L.fmt_it(it), flush=True)
fs = fragsets(pool, 'PHY_1V8', (-50.0, 200.0, -100.0, 100.0))
print('PHY_1V8 fragments:', [len(f) for f in fs], flush=True)
# what connects at the arm's far end: pads of PHY_1V8
for it in pool[0]:
    if it[0] == 'pad' and it[1] == 'PHY_1V8':
        print('pad:', it[2], flush=True)
