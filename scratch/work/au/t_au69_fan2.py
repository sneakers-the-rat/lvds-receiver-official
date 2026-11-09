"""t_au69: SCL fanout to pad-edge goal (66.2,2.08) in au67 state."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src67 = open('scratch/work/au/t_au67_pin2.py').read()
exec(src67.split("J = entry_astar")[0], g)
pool = g['pool']
fastest = g['fastest']
J = fastest('I2C_SCL', ((0, 1, 2), 69.35, 1.40), (0, 66.2, 2.08),
            hw=0.10)
print('fanout to (66.2,2.08):', 'FOUND' if J else 'NONE', flush=True)
if J:
    print('  vias', J['vias'],
          [(r['layer'], r['pts'][0], r['pts'][-1]) for r in J['runs']],
          flush=True)
    out = json.load(open('scratch/work/au/heals_au67.json'))
    out['scl_ffan'] = J
    json.dump(out, open('scratch/work/au/heals_au67.json', 'w'))
print('done')
