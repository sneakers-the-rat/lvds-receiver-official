"""t_au68: probe SCL fanout corridor in the au67 final state."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src67 = open('scratch/work/au/t_au67_pin2.py').read()
exec(src67.split("J = entry_astar")[0], g)
pool = g['pool']
import t_ai_lib as L
cells = [(69.35, 1.4), (68.8, 1.42), (68.3, 1.45), (67.8, 1.5),
         (67.4, 1.58), (67.0, 1.62), (66.6, 1.63), (66.3, 1.8),
         (66.15, 1.9), (66.025, 2.1), (66.4, 1.4), (67.9, 1.75),
         (68.6, 1.7), (69.0, 1.6)]
for (x, y) in cells:
    m, w = L.pt_margin(0, x, y, 'I2C_SCL', 0.10,
                       [o for o in pool[0] if o[1] != 'I2C_SCL'])
    print(f'F ({x},{y}): {m:+.3f} vs {L.fmt_it(w)}', flush=True)
print('done')
