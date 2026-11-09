import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av30'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
make_astar = g['make_astar']
# sites: (XO pad x, y) -> goals
tests = [
    ((60.75, 33.0), 'site A (56.5,33) r0'),
    ((60.5, 6.75), 'site B (60.5,11) r90'),
    ((51.0, 25.25), 'site C (51,29.5) r90'),
    ((62.25, 1.5), 'site D (58,1.5) r0'),
]
goals = [(1, 68.875, 20.375), (1, 73.125, 13.5)]
for (sx, sy), name in tests:
    a = make_astar((min(sx, 66) - 2, 76.0, min(sy, 12) - 3, max(sy, 21) + 3),
                   step=0.05)
    for gl, gx, gy in goals:
        J = a('XO', ((0, 1, 2), sx, sy), (gl, gx, gy), 0.10)
        print(f'{name} -> ({gx},{gy}): ' +
              ('NONE' if J is None else
               f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'),
              flush=True)
print('done', flush=True)
