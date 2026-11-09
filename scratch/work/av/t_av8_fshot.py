"""t_av8: F-start dip shots for XO. Pool: staircase (19) ripped."""
import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av8'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
make_astar = g['make_astar']
gate_pairs = g['gate_pairs']
import t_ai_lib as L

R2 = lambda v: round(v, 3)
STUB = (73.875, 11.625, 73.875, 12.875)
VERT = (73.875, 12.875, 73.875, 16.375)
n = 0
for it in list(pool[1]):
    if it[0] == 'seg' and it[1] == 'RBIAS':
        if tuple(R2(v) for v in it[2]) not in (STUB, VERT):
            pool[1].remove(it)
            n += 1
print(f'ripped {n} staircase segs', flush=True)

aF = make_astar((68.3, 76.2, 18.9, 26.3), step=0.025)
for start in (((0,), 71.625, 25.625), ((0, 2), 71.625, 25.625),
              ((0,), 71.875, 19.625)):
    J = aF('XO', start, (1, 68.875, 20.375), 0.10)
    print(f'start={start[0]}: ' +
          ('NONE' if J is None else
           f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'),
          flush=True)
    if J is not None:
        print('  worst pairs vs pool:', flush=True)
        for (m, l, it, o) in gate_pairs(J, 'XO', 0.10):
            print(f'    {m:+.3f} L{l} {L.fmt_it(it)} vs {L.fmt_it(o)}',
                  flush=True)
        break
print('done', flush=True)
