"""t_av23: iterative dip/ride separation. Each round: dip A* runs
with inflated dummy walls over all previously-found dip paths;
if the ride then fits, stop. State: rip19 + C49 + DIR re-lay."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av23'}
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

a_dip = make_astar((66.5, 76.0, 14.5, 27.0), step=0.025)
a_rb = make_astar((67.0, 75.0, 10.5, 22.5), step=0.025)


def remove_journey(name):
    net, hw = NET_HW[name]
    its = journey_items_dense(JOURNEYS[name], net, hw=hw)
    for l in range(3):
        for it in its[l]:
            NEW[l].remove(it)
            pool[l].remove(it)
    del JOURNEYS[name]
    del NET_HW[name]


def wall_from(J, net, hw, inflate=0.30):
    """Inflated dummy items replicating journey J's copper."""
    its = journey_items_dense(J, net, hw=hw)
    out = []
    for l in range(3):
        for it in its[l]:
            if it[0] == 'seg':
                x1, y1, x2, y2, h = it[2]
                out.append((l, ('seg', 'BLOCK_RSVD',
                                (x1, y1, x2, y2, h + inflate), 0.2)))
            elif it[0] == 'via':
                x, y, r = it[2]
                out.append((l, ('via', 'BLOCK_RSVD',
                                (x, y, r + inflate), 0.2)))
    return out


walls = []
found = False
for rnd in range(5):
    J = a_dip('XO', ((2,), 71.875, 19.625), (1, 68.875, 20.375), 0.10)
    if J is None:
        print(f'round {rnd}: dip NONE (walls={len(walls)})', flush=True)
        break
    print(f'round {rnd}: dip vias={J["vias"]} runs='
          f'{[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
          flush=True)
    if not try_emit('xo_bridge', J, 'XO', 0.10):
        print(f'round {rnd}: dip gate refused', flush=True)
        break
    Jr = a_rb('RBIAS', ((0, 1, 2), 73.875, 11.625), (2, 69.625, 20.625),
              0.125)
    print(f'round {rnd}: ride ' +
          ('NONE' if Jr is None else
           f'vias={Jr["vias"]} runs={[(r["layer"], len(r["pts"])) for r in Jr["runs"]]}'),
          flush=True)
    if Jr is not None and try_emit('rbias_relay', Jr, 'RBIAS', 0.125):
        print(f'round {rnd}: PAIR FOUND', flush=True)
        xo = fragments('XO', (63, 94, 7, 29))
        rb = fragments('RBIAS', (63, 80, 9, 26))
        print(f'XO frags={len(xo)} RBIAS frags={len(rb)}', flush=True)
        json.dump({'dip': J, 'ride': Jr},
                  open('scratch/work/av/pair_av23.json', 'w'))
        found = True
        break
    # block this dip path and retry
    w = wall_from(J, 'XO', 0.10)
    remove_journey('xo_bridge')
    for l, it in w:
        pool[l].append(it)
        walls.append((l, it))
    print(f'round {rnd}: dip path walled ({len(w)} items)', flush=True)
print('FOUND' if found else 'NOT FOUND', flush=True)
