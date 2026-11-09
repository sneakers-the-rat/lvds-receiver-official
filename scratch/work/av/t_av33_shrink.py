import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av33'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
make_astar = g['make_astar']
try_emit = g['try_emit']
fragments = g['fragments']
C = g['C']
import t_ai_lib as L
rip = [it for it in pool[1] if it[0] == 'seg' and it[1] == 'RBIAS']
assert len(rip) == 19
for it in rip:
    pool[1].remove(it)
print('staircase ripped', flush=True)
# Shrink C22 (72.5,18) and C24 (68.75,18) pads 0603 -> 0402:
# pads move from +-0.775 to +-0.5, size 0.5x0.55.
def shrink_pad(net, old_cx, new_cx, cy=18.0):
    for l in range(3):
        for it in list(pool[l]):
            if it[0] == 'pad' and it[1] == net:
                cc = C(it)
                if abs(cc[0] - old_cx) < 0.01 and abs(cc[1] - cy) < 0.01:
                    pool[l].remove(it)
                    pool[l].append(('pad', net,
                                     (new_cx, cy, 0.25, 0.275, 0), it[3]))
                    return True
    return False
# C22: PHY_1V8 pad (71.725,18) -> (72.0,18); GND pad (73.275,18) -> (73.0,18)
# C24: +3V3A pad (67.975,18) -> (68.25,18); GND pad (69.525,18) -> (69.25,18)
moves = [('PHY_1V8', 71.725, 72.0), ('GND', 73.275, 73.0),
         ('+3V3A', 67.975, 68.25), ('GND', 69.525, 69.25)]
for net, o, n in moves:
    # GND pads are ambiguous by net alone; match by old centre x AND
    # the C22/C24 row (y=18) - both GND pads handled by x order.
    ok = shrink_pad(net, o, n)
    print(f'  shrink {net} {o} -> {n}: {ok}', flush=True)
    assert ok
print('C22+C24 shrunk in model', flush=True)
a_dip = make_astar((66.0, 75.0, 17.0, 27.5), step=0.025)
J = a_dip('XO', ((0, 1, 2), 71.625, 25.625), (1, 68.875, 20.375), 0.10)
print('dip: ' + ('NONE' if J is None else
      f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'), flush=True)
if J is not None and try_emit('xo_bridge', J, 'XO', 0.10):
    xo = fragments('XO', (63, 94, 7, 29))
    print(f'XO frags={len(xo)}', flush=True)
    a_rb = make_astar((67.0, 75.0, 10.5, 22.5), step=0.025)
    Jr = a_rb('RBIAS', ((0, 1, 2), 73.875, 11.625), (2, 69.625, 20.625), 0.125)
    print('ride: ' + ('NONE' if Jr is None else
          f'vias={Jr["vias"]} runs={[(r["layer"], len(r["pts"])) for r in Jr["runs"]]}'), flush=True)
    if Jr is not None and try_emit('rbias_relay', Jr, 'RBIAS', 0.125):
        print('PAIR FOUND (C22/C24 shrink + F dip)', flush=True)
        json.dump({'dip': J, 'ride': Jr}, open('scratch/work/av/pair_av33.json', 'w'))
print('done', flush=True)
