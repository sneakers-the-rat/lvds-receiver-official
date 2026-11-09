"""t_av19: multi-layer A* XO (87.5,10.75) -> notch via (76.0,10.625).
Pool: au93 state with RBIAS staircase (19) ripped, no ride."""
import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av19'}
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
print(f'ripped {n}', flush=True)

a = make_astar((74.0, 89.0, 8.5, 13.5), step=0.025)
for gl in (1, 2, 0):
    J = a('XO', ((0, 1, 2), 87.5, 10.75), (gl, 76.0, 10.625), 0.10)
    print(f'goal layer {gl}: ' +
          ('NONE' if J is None else
           f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'),
          flush=True)
    if J is not None:
        for (m, l, it, o) in gate_pairs(J, 'XO', 0.10):
            print(f'    {m:+.3f} L{l} {L.fmt_it(it)} vs {L.fmt_it(o)}',
                  flush=True)
        break
print('done', flush=True)
