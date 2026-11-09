import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av35'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
C = g['C']
import t_ai_lib as L
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
# probe: F track-point margin (seg of zero length approx via via r0.1)
pts = [(71.625, 25.0), (71.625, 23.5), (71.625, 22.0), (71.625, 20.5),
       (71.625, 19.3), (71.9, 19.3), (72.1, 19.0), (72.1, 18.65),
       (71.6, 18.6), (71.2, 18.6), (70.95, 18.5), (70.6, 18.6),
       (70.3, 18.6)]
for (x, y) in pts:
    v = ('via', 'XO', (x, y, 0.10), 0.2)
    res = []
    for o in pool[0]:
        if o[1] == 'XO':
            continue
        m = g['item_margin'](0, v, [o])
        if m < 0.25:
            res.append((m, o))
    res.sort(key=lambda t: t[0])
    s = '; '.join(f'{m:+.3f} {L.fmt_it(o)}' for m, o in res[:2])
    print(f'({x},{y}): {s if s else "clear"}', flush=True)
print('done', flush=True)
