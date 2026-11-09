import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av31'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
make_astar = g['make_astar']
tests = [
    ((60.5, 6.75), (58.0, 70.5, 3.0, 22.5), 'site B XO pad (60.5,6.75)'),
    ((62.25, 1.5), (58.0, 70.5, -2.0, 22.5), 'site D XO pad (62.25,1.5)'),
]
for (sx, sy), box, name in tests:
    a = make_astar(box, step=0.025)
    J = a('XO', ((0, 1, 2), sx, sy), (1, 68.875, 20.375), 0.10)
    print(f'{name} -> tail: ' +
          ('NONE' if J is None else
           f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'),
          flush=True)
print('done', flush=True)
