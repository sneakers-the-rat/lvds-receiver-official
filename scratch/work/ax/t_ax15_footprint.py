"""t_ax15: find the footprint owning the pad at (66.3,6.75); print its
rotation and real pad sizes; print the +3V3D jog track's real width
and KiCad-geometry distance to that pad."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import math

b = pcbnew.LoadBoard(BOARD)
target = None
for fp in b.GetFootprints():
    for p in fp.Pads():
        px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
        if abs(px - 66.3) < 0.01 and abs(py - 6.75) < 0.01:
            target = (fp, p)
if target:
    fp, p = target
    print('footprint', fp.GetReference(), 'at',
          fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6,
          'rot', fp.GetOrientationDegrees(), flush=True)
    print(f"  pad net={p.GetNetname()} size="
          f"({p.GetSize().x/1e6:.3f}x{p.GetSize().y/1e6:.3f}) "
          f"local rot {p.GetOrientationDegrees()}", flush=True)
for t in b.GetTracks():
    if t.GetNetname() != '+3V3D':
        continue
    s = t.GetStart()
    e = t.GetEnd()
    sx, sy = s.x / 1e6, s.y / 1e6
    ex, ey = e.x / 1e6, e.y / 1e6
    if (abs(sx - 67.55) < 0.01 and abs(sy - 7.25) < 0.01) or \
       (abs(ex - 67.55) < 0.01 and abs(ey - 7.25) < 0.01):
        print(f'track ({sx:.3f},{sy:.3f})->({ex:.3f},{ey:.3f}) '
              f'w={t.GetWidth()/1e6:.3f} layer={t.GetLayerName()}',
              flush=True)
