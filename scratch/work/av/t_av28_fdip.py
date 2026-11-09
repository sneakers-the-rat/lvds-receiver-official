import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av28'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
make_astar = g['make_astar']
try_emit = g['try_emit']
fragments = g['fragments']
C = g['C']
R2 = lambda v: round(v, 3)
rip = [it for it in pool[1] if it[0] == 'seg' and it[1] == 'RBIAS']
assert len(rip) == 19
for it in rip:
    pool[1].remove(it)
def find_pad(net, cx, cy=19.5):
    for l in range(3):
        for it in pool[l]:
            if it[0] == 'pad' and it[1] == net:
                cc = C(it)
                if abs(cc[0] - cx) < 0.01 and abs(cc[1] - cy) < 0.01:
                    return l, it
    raise AssertionError(net)
for net, cx in (('+3V3A', 69.225), ('GND', 70.775)):
    l, it = find_pad(net, cx)
    pool[l].remove(it)
    kind, ntn, (ccx, ccy, hw_, hh, rot), clr = it
    pool[l].append(('pad', ntn, (ccx + 0.5, ccy, hw_, hh, rot), clr))
for l in range(3):
    for it in list(pool[l]):
        if it[0] == 'seg' and it[1] == '+3V3A':
            x1, y1, x2, y2, hw_ = it[2]
            if (abs(x2 - 69.225) < 0.01 and abs(y2 - 19.5) < 0.01
                    and abs(hw_ - 0.150) < 0.001):
                pool[l].remove(it)
ast = make_astar((66.0, 74.0, 15.0, 23.0), step=0.025)
J = ast('+3V3A', ((0,), 69.725, 19.5), (0, 69.225, 19.5), 0.15)
assert try_emit('c49_web_v3a', J, '+3V3A', 0.15)
DIR_SEG = (71.375, 19.125, 68.875, 29.0)
for it in list(pool[2]):
    if it[0] == 'seg' and it[1] == 'ULPI_DIR' \
            and tuple(R2(v) for v in it[2][:4]) == DIR_SEG:
        pool[2].remove(it)
a_dir = make_astar((68.3, 74.8, 18.6, 29.6), step=0.025)
J = a_dir('ULPI_DIR', ((2,), 71.375, 19.125), (2, 68.875, 29.0), 0.10)
assert try_emit('dir_tail_relay', J, 'ULPI_DIR', 0.10)
print('base state ready', flush=True)
a_dip = make_astar((66.0, 75.0, 18.0, 27.5), step=0.025)
J = a_dip('XO', ((0, 1, 2), 71.625, 25.625), (1, 68.875, 20.375), 0.10)
print('F-via dip: ' + ('NONE' if J is None else
      f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'), flush=True)
if J is not None and try_emit('xo_bridge', J, 'XO', 0.10):
    xo = fragments('XO', (63, 94, 7, 29))
    print(f'XO frags={len(xo)}', flush=True)
    a_rb = make_astar((67.0, 75.0, 10.5, 22.5), step=0.025)
    Jr = a_rb('RBIAS', ((0, 1, 2), 73.875, 11.625), (2, 69.625, 20.625), 0.125)
    print('ride: ' + ('NONE' if Jr is None else
          f'vias={Jr["vias"]} runs={[(r["layer"], len(r["pts"])) for r in Jr["runs"]]}'), flush=True)
    if Jr is not None and try_emit('rbias_relay', Jr, 'RBIAS', 0.125):
        print('PAIR FOUND (F-via dip)', flush=True)
        json.dump({'dip': J, 'ride': Jr}, open('scratch/work/av/pair_av28.json', 'w'))
print('done', flush=True)
