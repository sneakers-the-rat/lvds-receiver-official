"""t_au61: field slice for heal1 in v6 model (exit placed)."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src60 = open('scratch/work/au/t_au60_v6.py').read()
exec(src60.split("\nout = {")[0], g)
pool = g['pool']
import t_ai_lib as L
import numpy as np
for x in (68.3, 68.6, 68.9):
    print(f'--- x={x} (net +3V3A, track hw0.1) ---', flush=True)
    for y in np.arange(2.0, 5.01, 0.25):
        y = round(float(y), 2)
        cells = []
        for l in range(3):
            m, w = L.pt_margin(l, x, y, '+3V3A', 0.10,
                               [o for o in pool[l] if o[1] != '+3V3A'])
            cells.append(f'L{l} {m:+.2f}')
        print(f'  y={y}: ' + ' | '.join(cells), flush=True)
print('done')
