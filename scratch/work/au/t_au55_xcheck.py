"""t_au55: cross-check - au40's own astar on the au53 pool."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
# build au53 pool (minus heal1: stop before heal1 by splitting source)
g53 = {'__name__': 'p53'}
src53 = open('scratch/work/au/t_au53_exitmask.py').read()
head53 = src53.split("J = run_astar('+3V3A'")[0]
exec(head53, g53)
pool = g53['pool']
print('au53 pool (bheal+hop, no heal1) ready', flush=True)
# au40 machinery
g40 = {'__name__': 'j2'}
src40 = open('scratch/work/au/t_au40_joint2.py').read()
exec(src40.split("JOBS = {")[0], g40)
g40['POOL'] = pool
J = g40['astar']('CAP_CLK', ((0, 1, 2), 70.2, 1.8), (2, 69.55, 2.70))
print('au40 astar exit on au53 pool:', 'FOUND' if J else 'NONE',
      flush=True)
if J:
    print('  vias', J['vias'],
          [(r['layer'], r['pts'][0], r['pts'][-1]) for r in J['runs']])
# and au53 run_astar on the same pool
J2 = g53['run_astar']('CAP_CLK', ((0, 1, 2), 70.2, 1.8), (2, 69.55, 2.70))
print('au53 run_astar exit on same pool:', 'FOUND' if J2 else 'NONE',
      flush=True)
