"""t_av9: leg-by-leg diagnosis of the long dip.
Pool: staircase (19) ripped. Legs: B stub->viafit cell,
F via-disc->viafit cell, In2 viafit cell->{north waypoints, goal}."""
import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av9'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
make_astar = g['make_astar']

R2 = lambda v: round(v, 3)
STUB = (73.875, 11.625, 73.875, 12.875)
VERT = (73.875, 12.875, 73.875, 16.375)
pool = g['pool']
n = 0
for it in list(pool[1]):
    if it[0] == 'seg' and it[1] == 'RBIAS':
        if tuple(R2(v) for v in it[2]) not in (STUB, VERT):
            pool[1].remove(it)
            n += 1
print(f'ripped {n}', flush=True)

VIA = (73.925, 21.475)
a = make_astar((68.3, 76.2, 18.9, 26.3), step=0.025)


def shot(tag, start, goal, lock=None):
    J = a('XO', start, goal, 0.10, layer_lock=lock)
    print(f'{tag}: ' +
          ('NONE' if J is None else
           f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'),
          flush=True)
    return J


shot('B leg stub->via', ((2,), 71.875, 19.625), (2, VIA[0], VIA[1]),
     lock=(False, False, True))
shot('F leg disc->via', ((0,), 71.625, 25.625), (0, VIA[0], VIA[1]),
     lock=(True, False, False))
shot('In2 leg via->(71.0,24.3)', ((1,), VIA[0], VIA[1]), (1, 71.0, 24.3),
     lock=(False, True, False))
shot('In2 leg via->(69.6,24.3)', ((1,), VIA[0], VIA[1]), (1, 69.6, 24.3),
     lock=(False, True, False))
shot('In2 leg via->(69.4,22.5)', ((1,), VIA[0], VIA[1]), (1, 69.4, 22.5),
     lock=(False, True, False))
shot('In2 leg (69.4,22.5)->goal', ((1,), 69.4, 22.5),
     (1, 68.875, 20.375), lock=(False, True, False))
shot('In2 leg via->goal direct', ((1,), VIA[0], VIA[1]),
     (1, 68.875, 20.375), lock=(False, True, False))
shot('In2 leg via->S (74.6,19.6)', ((1,), VIA[0], VIA[1]),
     (1, 74.6, 19.6), lock=(False, True, False))
print('done', flush=True)
