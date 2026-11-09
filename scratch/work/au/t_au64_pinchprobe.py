"""t_au64: probe heal1 hand-path cells in v6 model (exit placed)."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src60 = open('scratch/work/au/t_au60_v6.py').read()
exec(src60.split("\nout = {")[0], g)
pool = g['pool']
import t_ai_lib as L
cells = [(67.975, 2.75), (68.3, 2.72), (68.4, 2.65), (68.52, 2.95),
         (68.58, 3.3), (68.8, 3.8), (69.0, 4.3), (69.125, 4.375),
         (68.55, 3.1), (68.65, 3.55)]
for (x, y) in cells:
    m, w = L.pt_margin(0, x, y, '+3V3A', 0.10,
                       [o for o in pool[0] if o[1] != '+3V3A'])
    print(f'F ({x},{y}): {m:+.3f} vs {L.fmt_it(w)}', flush=True)
print('done')
