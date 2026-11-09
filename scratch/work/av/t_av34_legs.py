import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av34'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
make_astar = g['make_astar']
C = g['C']
import t_ai_lib as L
import numpy as np
rip = [it for it in pool[1] if it[0] == 'seg' and it[1] == 'RBIAS']
assert len(rip) == 19
for it in rip:
    pool[1].remove(it)
def shrink_pad(net, old_cx, new_cx, cy=18.0):
    for l in range(3):
        for it in list(pool[l]):
            if it[0] == 'pad' and it[1] == net:
                cc = C(it)
                if abs(cc[0] - old_cx) < 0.01 and abs(cc[1] - cy) < 0.01:
                    pool[l].remove(it)
                    pool[l].append(('pad', net, (new_cx, cy, 0.25, 0.275, 0), it[3]))
                    return True
    return False
for net, o, n in [('PHY_1V8', 71.725, 72.0), ('GND', 73.275, 73.0),
                  ('+3V3A', 67.975, 68.25), ('GND', 69.525, 69.25)]:
    assert shrink_pad(net, o, n)
print('shrunk', flush=True)
a_f = make_astar((66.0, 75.0, 17.0, 27.5), step=0.025)
J1 = a_f('XO', ((0,), 71.625, 25.625), (0, 70.15, 18.6), 0.10,
         layer_lock=(True, False, False))
print('F leg: ' + ('NONE' if J1 is None else f'{len(J1["runs"][0]["pts"])} pts'), flush=True)
a_i = make_astar((66.0, 75.0, 17.0, 27.5), step=0.025)
J2 = a_i('XO', ((1,), 70.15, 18.6), (1, 68.875, 20.375), 0.10,
         layer_lock=(False, True, False))
print('In2 leg: ' + ('NONE' if J2 is None else f'{len(J2["runs"][0]["pts"])} pts'), flush=True)
# via field at the dive
for l in range(3):
    v = ('via', 'XO', (70.15, 18.6, 0.25), 0.2)
    res = []
    for o in pool[l]:
        if o[1] == 'XO':
            continue
        m = g['item_margin'](l, v, [o])
        if m < 0.3:
            res.append((m, o))
    res.sort(key=lambda t: t[0])
    for m, o in res[:3]:
        print(f'  dive L{l} {m:+.3f} vs {L.fmt_it(o)}', flush=True)
print('done', flush=True)
