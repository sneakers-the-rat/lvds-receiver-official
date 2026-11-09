import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av29'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
make_astar = g['make_astar']
try_emit = g['try_emit']
fragments = g['fragments']
gate_pairs = g['gate_pairs']
import t_ai_lib as L
rip = [it for it in pool[1] if it[0] == 'seg' and it[1] == 'RBIAS']
assert len(rip) == 19
for it in rip:
    pool[1].remove(it)
print('staircase ripped (no C49 move, no DIR re-lay)', flush=True)
# viafit probe at the candidates (all layers, vs foreign items)
from collections import defaultdict
import math
def via_field(x, y):
    worst = {}
    for l in range(3):
        v = ('via', 'XO', (x, y, 0.25), 0.2)
        m = 9.9
        worst_it = None
        for o in pool[l]:
            if o[1] == 'XO':
                continue
            mm = g['item_margin'](l, v, [o])
            if mm < m:
                m = mm
                worst_it = o
        worst[l] = (m, worst_it)
    return worst
for (x, y) in [(68.3, 20.6), (68.25, 20.55), (68.35, 20.65),
               (68.3, 20.5), (68.2, 20.6), (68.4, 20.6), (68.3, 20.7)]:
    w = via_field(x, y)
    print(f'via ({x},{y}): ' + ' '.join(
        f'L{l}={w[l][0]:+.3f}({L.fmt_it(w[l][1]) if w[l][1] else "-"})'
        for l in range(3)), flush=True)
a_b = make_astar((66.5, 74.0, 16.0, 23.0), step=0.025)
a_i = make_astar((66.5, 74.0, 18.0, 22.5), step=0.025)
dip_done = False
for (vx, vy) in [(68.3, 20.6), (68.25, 20.55), (68.35, 20.65),
                 (68.3, 20.5), (68.2, 20.6), (68.4, 20.6), (68.3, 20.7)]:
    Jb = a_b('XO', ((2,), 71.875, 19.625), (2, vx, vy), 0.10,
             layer_lock=(False, False, True))
    if Jb is None:
        print(f'  via ({vx},{vy}): B leg NONE', flush=True)
        continue
    Ji = a_i('XO', ((1,), vx, vy), (1, 68.875, 20.375), 0.10,
             layer_lock=(False, True, False))
    if Ji is None:
        print(f'  via ({vx},{vy}): In2 leg NONE', flush=True)
        continue
    J = dict(vias=[[vx, vy]], runs=Jb['runs'] + Ji['runs'])
    print(f'  via ({vx},{vy}): composed runs='
          f'{[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
          flush=True)
    if try_emit('xo_bridge', J, 'XO', 0.10):
        xo = fragments('XO', (63, 94, 7, 29))
        print(f'  XO frags={len(xo)}', flush=True)
        if len(xo) == 1:
            dip_done = True
            a_rb = make_astar((67.0, 75.0, 10.5, 22.5), step=0.025)
            Jr = a_rb('RBIAS', ((0, 1, 2), 73.875, 11.625),
                      (2, 69.625, 20.625), 0.125)
            print('  ride: ' + ('NONE' if Jr is None else
                  f'vias={Jr["vias"]} runs={[(r["layer"], len(r["pts"])) for r in Jr["runs"]]}'),
                  flush=True)
            if Jr is not None and try_emit('rbias_relay', Jr, 'RBIAS', 0.125):
                print('PAIR FOUND (west dip)', flush=True)
                json.dump({'dip': J, 'ride': Jr},
                          open('scratch/work/av/pair_av29.json', 'w'))
            break
print('DIP DONE' if dip_done else 'DIP FAILED', flush=True)
