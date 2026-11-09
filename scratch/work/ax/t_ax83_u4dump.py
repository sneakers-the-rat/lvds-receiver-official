import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp248.kicad_pcb')
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp248.kicad_pcb')
for fp in b.GetFootprints():
    if fp.GetReference() == 'U4':
        print('U4 at', fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6,
              'rot', fp.GetOrientationDegrees(), flush=True)
        for p in fp.Pads():
            print(f"   pad {p.GetNumber()} {p.GetNetname()} "
                  f"({p.GetPosition().x / 1e6:.3f},"
                  f"{p.GetPosition().y / 1e6:.3f})", flush=True)
for lay, nm in ((0, 'F'), (1, 'In2'), (2, 'B')):
    print(f'== {nm} items in (66,72,33,39):', flush=True)
    seen = set()
    for it in pool[lay]:
        d = it[2]
        if 66 < d[0] < 72 and 33 < d[1] < 39:
            s = L.fmt_it(it)
            if s not in seen:
                seen.add(s)
                print('  ', s, flush=True)
