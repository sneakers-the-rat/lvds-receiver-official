"""t_az16: XI pass design verification.
Pool = faithful exp251 + PHY_1V8A notch re-lay ONLY:
 rip notch via (75.737,10.75), F stub segs, B head seg;
 add via (75.20,10.40), F stub (75.75,11.562)->(75.45,11.15)
 ->(75.20,10.40), B seg (75.20,10.40)->(75.30,11.35).
Then: fragments(PHY_1V8A) must stay 1 in the district; gate the
notch items; A* XI U7.28 -> arc goals; gate the XI journey.
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'


def seg(net, x1, y1, x2, y2, hw=0.10, clr=0.2):
    return ('seg', net, (x1, y1, x2, y2, hw), clr)


def via(net, x, y, r=0.25, clr=0.2):
    return ('via', net, (x, y, r), clr)


def gate_items(items_by_layer, label):
    worst = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                m = item_margin(l, it, [o])
                if m < 0.30:
                    worst.append((round(m, 3), l, it, o))
    worst.sort(key=lambda t: t[0])
    print(f'{label}: {len(worst)} pairs < 0.30; worst 8:')
    for w in worst[:8]:
        print('   ', w)
    return worst


pool = load_board_pool(BOARD)
print('1V8A fragments faithful:',
      len(fragments('PHY_1V8A', (58.0, 96.0, -30.0, 34.0))))
n_rip = 0
n_rip += rip_items([it for l in range(3) for it in pool[l]
                    if it[1] == 'PHY_1V8A' and it[0] == 'via'
                    and abs(it[2][0] - 75.737) < 0.01
                    and abs(it[2][1] - 10.75) < 0.01])
n_rip += rip_items([it for it in pool[0]
                    if it[1] == 'PHY_1V8A' and it[0] == 'seg'
                    and C(it)[0] > 75.6 and C(it)[1] > 10.6])
n_rip += rip_items([it for it in pool[2]
                    if it[1] == 'PHY_1V8A' and it[0] == 'seg'
                    and abs(it[2][0] - 75.737) < 0.01
                    and abs(it[2][1] - 10.75) < 0.01])
print('ripped notch items (entries):', n_rip)
NEW1 = {0: [via('PHY_1V8A', 75.20, 10.40, 0.25, 0.25),
            seg('PHY_1V8A', 75.75, 11.562, 75.45, 11.15, 0.10, 0.25),
            seg('PHY_1V8A', 75.45, 11.15, 75.20, 10.40, 0.10, 0.25)],
        1: [via('PHY_1V8A', 75.20, 10.40, 0.25, 0.25)],
        2: [via('PHY_1V8A', 75.20, 10.40, 0.25, 0.25),
            seg('PHY_1V8A', 75.20, 10.40, 75.30, 11.35, 0.10, 0.25)]}
add_items(NEW1)
print('1V8A fragments after re-lay:',
      len(fragments('PHY_1V8A', (58.0, 96.0, -30.0, 34.0))))
gate_items(NEW1, 'notch re-lay gate')

astar = make_astar((70.0, 88.0, 8.0, 23.0), 0.125)
J = None
for (gl, gx, gy) in [(2, 75.625, 18.625), (0, 75.72, 18.73),
                     (2, 78.375, 21.125)]:
    r = astar('XI', ((0,), 76.25, 11.562), (gl, gx, gy), 0.10)
    print(f'XI -> L{gl} ({gx},{gy}):',
          f'FOUND vias={r["vias"]}' if r else 'none')
    if r and J is None:
        J = r
if J:
    for rn in J['runs']:
        print(f"   L{rn['layer']} {len(rn['pts'])} pts "
              f"{rn['pts'][0]} -> {rn['pts'][-1]}")
    print('XI journey gate_pairs:', gate_pairs(J, 'XI', 0.10))
    items = journey_items_dense(J, 'XI', hw=0.10)
    gate_items(items, 'XI journey gate')
print('=== done ===')
