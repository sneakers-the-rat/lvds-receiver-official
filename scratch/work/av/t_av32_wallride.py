import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av32'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
NEW = g['NEW']
JOURNEYS = g['JOURNEYS']
NET_HW = g['NET_HW']
make_astar = g['make_astar']
journey_items_dense = g['journey_items_dense']
try_emit = g['try_emit']
fragments = g['fragments']
rip = [it for it in pool[1] if it[0] == 'seg' and it[1] == 'RBIAS']
assert len(rip) == 19
for it in rip:
    pool[1].remove(it)
a_rb = make_astar((67.0, 75.0, 10.5, 22.5), step=0.025)
Jr0 = a_rb('RBIAS', ((0, 1, 2), 73.875, 11.625), (2, 69.625, 20.625), 0.125)
assert Jr0 is not None
print(f'ride (solo): vias={Jr0["vias"]} runs={[(r["layer"], len(r["pts"])) for r in Jr0["runs"]]}', flush=True)
def wall_from(J, net, hw, inflate):
    its = journey_items_dense(J, net, hw=hw)
    out = []
    for l in range(3):
        for it in its[l]:
            if it[0] == 'seg':
                x1, y1, x2, y2, h = it[2]
                out.append((l, ('seg', 'BLOCK_RSVD', (x1, y1, x2, y2, h + inflate), 0.2)))
            elif it[0] == 'via':
                x, y, r = it[2]
                out.append((l, ('via', 'BLOCK_RSVD', (x, y, r + inflate), 0.2)))
    return out
a_dip = make_astar((66.5, 76.0, 14.5, 27.0), step=0.025)
for inflate in (0.25, 0.40, 0.15):
    walls = wall_from(Jr0, 'RBIAS', 0.125, inflate)
    for l, it in walls:
        pool[l].append(it)
    J = a_dip('XO', ((2,), 71.875, 19.625), (1, 68.875, 20.375), 0.10)
    print(f'inflate={inflate}: dip ' + ('NONE' if J is None else
          f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'), flush=True)
    for l, it in walls:
        pool[l].remove(it)
    if J is not None:
        if try_emit('xo_bridge', J, 'XO', 0.10):
            Jr = a_rb('RBIAS', ((0, 1, 2), 73.875, 11.625), (2, 69.625, 20.625), 0.125)
            print('  ride after dip: ' + ('NONE' if Jr is None else
                  f'vias={Jr["vias"]} runs={[(r["layer"], len(r["pts"])) for r in Jr["runs"]]}'), flush=True)
            if Jr is not None and try_emit('rbias_relay', Jr, 'RBIAS', 0.125):
                xo = fragments('XO', (63, 94, 7, 29))
                print(f'  PAIR FOUND inflate={inflate}; XO frags={len(xo)}', flush=True)
                json.dump({'dip': J, 'ride': Jr}, open('scratch/work/av/pair_av32.json', 'w'))
                break
            # remove the emitted dip and try next inflation
            net, hw = NET_HW['xo_bridge']
            its = journey_items_dense(JOURNEYS['xo_bridge'], net, hw=hw)
            for l in range(3):
                for it in its[l]:
                    NEW[l].remove(it)
                    pool[l].remove(it)
            del JOURNEYS['xo_bridge']
            del NET_HW['xo_bridge']
print('done', flush=True)
