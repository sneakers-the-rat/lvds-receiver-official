"""t_ax14: U14 raw pad geometry from pcbnew + model margins of the
shipped +3V3D jog segs vs U14 pads."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

b = pcbnew.LoadBoard(BOARD)
for fp in b.GetFootprints():
    if fp.GetReference() == 'U14':
        print('U14 at', fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6,
              'rot', fp.GetOrientationDegrees(), flush=True)
        for p in fp.Pads():
            print(f"  pad net={p.GetNetname()} centre= "
                  f"({p.GetPosition().x/1e6:.3f},{p.GetPosition().y/1e6:.3f})"
                  f" size=({p.GetSize().x/1e6:.3f}x{p.GetSize().y/1e6:.3f})",
                  flush=True)
pool = load_board_pool()
jog = [it for it in pool[0] if it[1] == '+3V3D' and it[0] == 'seg'
       and abs(it[2][0] - 67.55) < 0.01 and abs(it[2][1] - 7.25) < 0.01]
pads = [it for it in pool[0] if it[0] == 'pad' and it[1] in
        ('GND', 'THR_DAC', 'HV_DAC') and it[2][0] < 67.2]
for s in jog:
    print('seg', L.fmt_it(s), flush=True)
    for p in pads:
        print(f'  margin vs {L.fmt_it(p)}: '
              f'{item_margin(0, s, [p]):+.3f}', flush=True)
