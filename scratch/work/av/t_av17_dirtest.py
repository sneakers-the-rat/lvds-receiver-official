"""t_av17: isolate the DIR tail A* failure."""
import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av17'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
make_astar = g['make_astar']
try_emit = g['try_emit']

R2 = lambda v: round(v, 3)
STUB = (73.875, 11.625, 73.875, 12.875)
VERT = (73.875, 12.875, 73.875, 16.375)
for it in list(pool[1]):
    if it[0] == 'seg' and it[1] == 'RBIAS':
        if tuple(R2(v) for v in it[2]) not in (STUB, VERT):
            pool[1].remove(it)
# C49 pads move (as t_av13)
PADS_OLD = {'+3V3A': (69.225, 19.5), 'GND': (70.775, 19.5)}
for net, (px, py) in PADS_OLD.items():
    for it in list(pool[0]):
        if it[0] == 'pad' and it[1] == net and \
                abs(it[2][0] - px) < 0.01 and abs(it[2][1] - py) < 0.01:
            pool[0].remove(it)
            pool[0].append(('pad', net, (px + 0.5 if net == 'GND'
                                         else px + 0.5, py,
                                         0.450, 0.475, 0.0), it[3]))
# remove DIR seg
for it in list(pool[2]):
    if it[0] == 'seg' and it[1] == 'ULPI_DIR' and \
            tuple(R2(v) for v in it[2]) == (71.375, 19.125, 68.875,
                                            29.0, 0.1):
        pool[2].remove(it)
        print('DIR seg removed', flush=True)

for step in (0.025, 0.05):
    a = make_astar((68.3, 72.2, 18.6, 29.6), step=step)
    J = a('ULPI_DIR', ((2,), 71.375, 19.125), (2, 68.875, 29.0), 0.10,
          layer_lock=(False, False, True))
    print(f'no dummies, step={step}: ' +
          ('NONE' if J is None else
           f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'),
          flush=True)

DUM = 'BLOCK_RSVD'
dummies = []
for l in range(3):
    dummies.append((l, ('via', DUM, (70.45, 20.25, 0.35), 0.2)))
dummies.append((2, ('seg', DUM, (71.875, 19.625, 70.45, 20.25, 0.15),
                    0.2)))
for l, it in dummies:
    pool[l].append(it)
for step in (0.025, 0.05):
    a = make_astar((68.3, 72.2, 18.6, 29.6), step=step)
    J = a('ULPI_DIR', ((2,), 71.375, 19.125), (2, 68.875, 29.0), 0.10,
          layer_lock=(False, False, True))
    print(f'with dummies, step={step}: ' +
          ('NONE' if J is None else
           f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'),
          flush=True)
print('done', flush=True)
