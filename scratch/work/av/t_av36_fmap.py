import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av36'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
C = g['C']
import numpy as np
import t_ai_lib as L
# rebuild the au71 field machinery for F layer, net XO
src71 = open('scratch/work/au/t_au71_phase2b.py').read()
g71 = {'__name__': 'av36b'}
# exec only up to make_astar def in au71 by capturing its globals:
exec(src71.split('def fragments')[0], g71)
# Instead: use make_astar from phase2y globals (it is in g)
make_astar = g['make_astar']
# Field dump: use a fresh astar object's internals is not exposed;
# emulate: track field G0 = min over foreign F items of df - req.
# df per item kind via t_ai_lib distance functions is complex; use
# item_margin on a seg probe: G_track(x,y) = min item_margin of a
# r0.10 disc (margin already subtracts clr) -> legal if >= 0.10-0.10?
# item_margin(via r0.1) = dist - fence_hw - 0.1 - 0.2; track legal
# iff dist - fence_hw - 0.2 >= 0.1 i.e. margin >= 0.0.
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
items = [o for o in pool[0] if o[1] != 'XO']
im = g['item_margin']
print('F track field, x 70.8..74.4 step 0.3, y 26.4..21.6 step -0.3')
print('   ' + ''.join(f'{(70.8 + 0.3 * i):4.1f}'[-4:] for i in range(13)))
for yi in range(17):
    y = 26.4 - 0.3 * yi
    row = ''
    for xi in range(13):
        x = 70.8 + 0.3 * xi
        v = ('via', 'XO', (x, y, 0.10), 0.2)
        m = min((im(0, v, [o]) for o in items), default=9.9)
        row += '  . ' if m >= 0.0 else '  # '
    print(f'{y:5.2f} {row}')
print('done', flush=True)
