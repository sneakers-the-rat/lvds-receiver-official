"""t_av24: bridge via XO's staircase vertical. ML A* from
(87.5,10.75) to (73.125,13.5) [a point ON frag-1's In2 vertical
seg] in the current state (staircase ripped). Then RBIAS ride.
Join verified by point-on-segment (fragments() is T-join blind),
and the endpoint lies on the seg so KiCad contact is real."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av24'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
NEW = g['NEW']
JOURNEYS = g['JOURNEYS']
NET_HW = g['NET_HW']
fragments = g['fragments']
make_astar = g['make_astar']
journey_items_dense = g['journey_items_dense']
try_emit = g['try_emit']
C = g['C']
import t_ai_lib as L
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

a_br = make_astar((72.0, 89.0, 9.0, 15.5), step=0.025)
JB = None
for gy in (13.5, 13.0, 14.0, 12.5, 14.5):
    JB = a_br('XO', ((0, 1, 2), 87.5, 10.75), (1, 73.125, gy), 0.10)
    print(f'bridge to (73.125,{gy}): ' +
          ('NONE' if JB is None else
           f'vias={JB["vias"]} runs={[(r["layer"], len(r["pts"])) for r in JB["runs"]]}'),
          flush=True)
    if JB is not None:
        break
if JB is not None:
    ok = try_emit('xo_bridge', JB, 'XO', 0.10)
    print(f'bridge emit: {ok}', flush=True)
    if ok:
        # point-on-segment verification vs the vertical
        import math
        end = JB['runs'][-1]['pts'][-1]
        d = abs(end[0] - 73.125)
        print(f'bridge end {end}: |dx| to vertical = {d:.3f}',
              flush=True)
        a_rb = make_astar((67.0, 75.0, 10.5, 22.5), step=0.025)
        Jr = a_rb('RBIAS', ((0, 1, 2), 73.875, 11.625),
                  (2, 69.625, 20.625), 0.125)
        print('ride: ' + ('NONE' if Jr is None else
              f'vias={Jr["vias"]} runs={[(r["layer"], len(r["pts"])) for r in Jr["runs"]]}'),
              flush=True)
        if Jr is not None and try_emit('rbias_relay', Jr, 'RBIAS',
                                        0.125):
            print('PAIR FOUND (staircase bridge)', flush=True)
            json.dump({'dip': JB, 'ride': Jr},
                      open('scratch/work/av/pair_av24.json', 'w'))
print('done', flush=True)
