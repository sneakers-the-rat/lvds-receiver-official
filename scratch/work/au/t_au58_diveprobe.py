"""t_au58: in heal1-F-only-placed model, probe viafit at grid pts."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au53_exitmask.py').read()
exec(src.split("J = entry_astar")[0], g)
pool = g['pool']
import t_ai_lib as L
import numpy as np
for x in np.arange(68.6, 70.01, 0.2):
    row = []
    for y in np.arange(2.2, 3.41, 0.2):
        ms = []
        for l in range(3):
            m, _ = L.pt_margin(l, round(float(x), 2), round(float(y), 2),
                               'CAP_CLK', 0.25,
                               [o for o in pool[l] if o[1] != 'CAP_CLK'])
            ms.append(m)
        row.append(min(ms))
    print(f'x={x:.1f} viafit-min y2.2..3.4:', ['%+.2f' % v for v in row],
          flush=True)
print('done')
