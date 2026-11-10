"""t_ba36: STP transition via takes the pocket (76.85,9.5)
(grid +0.061, t_ba34); full STP journey gated. Then GND
A* from C22 pad2 (77.3,9.67) on F west to the existing GND
via (71.30,10.40); fallback (70.92,9.97). If FOUND, gate
the GND journey exactly."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)
rip = []
for l in range(3):
    for it in pool[l]:
        if it[1] != 'ULPI_STP' or it[0] not in ('seg', 'via'):
            continue
        cc = C(it)
        if 75.5 <= cc[0] <= 78.5 and 7.0 <= cc[1] <= 14.0:
            rip.append(it)
        elif 0.5 < cc[1] < 7.5 and cc[0] > 72.0:
            rip.append(it)
rip_items(rip)

ST = json.load(open('scratch/work/ba/design_stp_south.json'))
runs = ST['runs']
bpts = [tuple(p) for p in runs[0]['pts']]
i_cut = min(range(len(bpts)),
            key=lambda i: (bpts[i][0] - 76.2) ** 2 + (bpts[i][1] - 10.5) ** 2)
head = [list(p) for p in bpts[:i_cut + 1]]
STP6 = {'runs': [{'layer': 2, 'pts': head + [[76.85, 9.5]]},
                 {'layer': 1, 'pts': [[76.85, 9.5], [77.2, 5.9]]}] +
        runs[2:],
        'vias': [[76.85, 9.5]] + ST['vias'][1:]}
JI = journey_items_dense(STP6, 'ULPI_STP', hw=0.10)


def gate(items_by_layer, label):
    ps = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                m = item_margin(l, it, [o])
                if m < 0.15:
                    ps.append((round(m, 3), LAYN[l], o[1],
                               (round(C(it)[0], 2), round(C(it)[1], 2)),
                               (round(C(o)[0], 2), round(C(o)[1], 2))))
    ps.sort(key=lambda t: t[0])
    n = sum(1 for p in ps if p[0] < 0)
    print(f'{label}: neg {n}, worst 6: {ps[:6]}')
    return n


n = gate(JI, 'STP6 (pocket transition)')
if n == 0:
    json.dump(STP6, open('scratch/work/ba/design_stp_south6.json', 'w'))
    add_items(JI)
    print('STP6 placed; frags', len(fragments('ULPI_STP', BOX)))
    astar = make_astar((64.0, 84.0, 4.0, 22.0), 0.05)
    for goal in [(71.30, 10.40), (70.92, 9.97)]:
        rr = astar('GND', ((0,), 77.3, 9.67), (0, goal[0], goal[1]), 0.10)
        print(f'GND A* -> {goal}:',
              'FOUND vias=' + str(rr['vias']) if rr else 'NONE')
        if rr:
            GJ = journey_items_dense(rr, 'GND', hw=0.10)
            m = gate(GJ, 'GND journey')
            if m == 0:
                json.dump(rr, open('scratch/work/ba/design_gnd_tie.json',
                                   'w'))
                print('GND tie saved')
            break
print('=== done ===')
