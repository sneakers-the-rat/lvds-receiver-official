import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
FULL = (-50.0, 200.0, -100.0, 100.0)
for tag, path in (('exp250', 'hw/pdlvds_rx.exp250.kicad_pcb'),
                  ('exp249', 'hw/pdlvds_rx.exp249.kicad_pcb')):
    pool = load_board_pool(path)
    for net in ('PHY_1V8A', '+3V3D'):
        fs = fragments(net, FULL)
        print(f'{tag} {net}: {len(fs)} frags',
              [len(f['items']) for f in fs], flush=True)
        for f in fs:
            if len(f['items']) <= 10:
                for (l, it) in f['items']:
                    print('   small:', 'FIB'[l], L.fmt_it(it), flush=True)
                print('   terms:', f['terms'], flush=True)
