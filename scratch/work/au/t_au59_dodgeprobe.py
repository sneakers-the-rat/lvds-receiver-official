"""t_au59: probe heal1 dodge-path cells in exit-placed model."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au43_phase1b.py').read()
exec(src.split("J40 = json.load")[0], g)
pool = g['pool']
journey_items_dense = g['journey_items_dense']
J40 = json.load(open('scratch/work/au/joint_au40.json'))
for nm in ('bheal', 'hop', 'exit'):
    J = J40['jobs'][nm]
    net = {'bheal': 'I2C_SCL', 'hop': 'I2C_SDA', 'exit': 'CAP_CLK'}[nm]
    hw = 0.125 if nm == 'hop' else 0.10
    for l, its in journey_items_dense(J, net, hw=hw).items():
        pool[l] += its
import t_ai_lib as L
cells = [(68.225, 2.75), (68.35, 2.95), (68.5, 3.13), (68.6, 3.3),
         (68.95, 3.45), (69.3, 3.6), (69.2, 4.0), (69.125, 4.375),
         (68.75, 3.3), (68.85, 3.2)]
for (x, y) in cells:
    m, w = L.pt_margin(0, x, y, '+3V3A', 0.10,
                       [o for o in pool[0] if o[1] != '+3V3A'])
    print(f'F ({x},{y}): {m:+.3f} vs {L.fmt_it(w)}', flush=True)
print('done')
