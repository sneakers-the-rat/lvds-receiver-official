"""t_au66: dump +3V3A F field (build_G) over the pinch box."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src65 = open('scratch/work/au/t_au65_pin.py').read()
exec(src65.split("J = fastest('+3V3A'")[0], g)
pool = g['pool']
build_G = g['build_G']
fxs, fys = g['fxs'], g['fys']
import t_au1_lib as U
# reservation via was added by t_au65 head? No - head stops before it.
# Re-add it: the head includes au40-exit removal only. Add reservation:
for l in range(3):
    pool[l].append(('via', 'CAP_CLK', (69.025, 2.8, 0.25), 0.2))
G = build_G('+3V3A')
F = G[0]
import numpy as np
print('     ' + ''.join(f'{x:5.0f}' for x in
      [68.3, 68.4, 68.5, 68.55, 68.6, 68.7, 68.8]))
for y in np.arange(2.6, 3.71, 0.1):
    row = []
    for x in (68.3, 68.4, 68.5, 68.55, 68.6, 68.7, 68.8):
        iy = int(round((y - (-0.5)) / 0.025))
        ix = int(round((x - 66.0) / 0.025))
        row.append(F[iy, ix])
    print(f'y={y:.2f} ' + ' '.join(f'{v:+.2f}' for v in row), flush=True)
print('done')
