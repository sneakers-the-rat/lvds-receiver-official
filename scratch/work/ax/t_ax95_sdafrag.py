import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
for tag, path in (('exp248', 'hw/pdlvds_rx.exp248.kicad_pcb'),
                  ('exp249', 'hw/pdlvds_rx.exp249.kicad_pcb')):
    pool = load_board_pool(path)
    fs = fragsets(pool, 'I2C_SDA', (60.0, 100.0, -30.0, 45.0))
    print(f'{tag}: {len(fs)} fragment(s)', flush=True)
    for f in fs:
        print('   size', len(f['items']), 'terms', f['terms'][:8],
              flush=True)
