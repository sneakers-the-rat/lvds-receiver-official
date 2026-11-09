import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard(BOARD)
for fp in b.GetFootprints():
    pos = fp.GetPosition()
    cx, cy = pos.x / 1e6, pos.y / 1e6
    if 65 < cx < 80 and -6 < cy < 16:
        print(f'{fp.GetReference()} at ({cx:.2f},{cy:.2f}) '
              f'fp={fp.GetFPID().GetLibItemName()}', flush=True)
    for p in fp.Pads():
        px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
        if 70.0 < px < 73.5 and 0.0 < py < 5.0:
            print(f'  pad {fp.GetReference()} net={p.GetNetname()} '
                  f'({px:.3f},{py:.3f})', flush=True)
# R20 current geometry
for fp in b.GetFootprints():
    if fp.GetReference() == 'R20':
        print('R20 at', fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6,
              'rot', fp.GetOrientationDegrees(),
              fp.GetFPID().GetLibItemName(), flush=True)
        for p in fp.Pads():
            print(f"  pad net={p.GetNetname()} "
                  f"({p.GetPosition().x/1e6:.3f},{p.GetPosition().y/1e6:.3f})"
                  f" size=({p.GetSize().x/1e6:.2f}x{p.GetSize().y/1e6:.2f})",
                  flush=True)
