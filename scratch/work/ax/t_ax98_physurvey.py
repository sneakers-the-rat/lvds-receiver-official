import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
fs = fragsets(pool, 'PHY_1V8A', (60.0, 100.0, -30.0, 45.0))
print(f'PHY_1V8A: {len(fs)} fragment(s)', flush=True)
for f in fs:
    print('   size', len(f['items']), 'terms', f['terms'], flush=True)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp249.kicad_pcb')
for ref in ('C16', 'C23', 'U7'):
    for fp in b.GetFootprints():
        if fp.GetReference() == ref:
            p = fp.GetPosition()
            print(f'{ref} at ({p.x / 1e6:.2f},{p.y / 1e6:.2f}) rot '
                  f'{fp.GetOrientationDegrees()}', flush=True)
            for pad in fp.Pads():
                pp = pad.GetPosition()
                print(f"   pad {pad.GetNumber()} {pad.GetNetname()} "
                      f"({pp.x / 1e6:.3f},{pp.y / 1e6:.3f})", flush=True)
