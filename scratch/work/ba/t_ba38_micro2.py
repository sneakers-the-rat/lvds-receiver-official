"""t_ba38: micro-grids in the final configuration.
Pool: exp252 + STP south ripped. STP7 transition via V on
a 0.025 grid x[76.42,76.68] y[8.98,9.22] (items: B descent
ext (76.2,10.5)->V, In2 V->(77.2,5.9), via V; tail NOT
included -- its gate is unchanged from t_ba23/t_ba36).
With the best V placed (full STP7), GND via G on a 0.025
grid x[76.95,77.30] y[9.45,9.85]: gate via + stub from
pad2 (77.3,9.67). Report feasible sets."""
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


def worst(items_by_layer, near=4.0):
    w, wo = 9.9, None
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                cc, ci = C(o), C(it)
                if abs(cc[0] - ci[0]) > near or abs(cc[1] - ci[1]) > near:
                    continue
                m = item_margin(l, it, [o])
                if m < w:
                    w, wo = m, (LAYN[l], o[1])
    return w, wo


def stp_partial(vx, vy):
    return {2: [('seg', 'ULPI_STP', (76.2, 10.5, vx, vy, 0.10), 0.2),
                ('via', 'ULPI_STP', (vx, vy, 0.25), 0.2)],
            1: [('seg', 'ULPI_STP', (vx, vy, 77.2, 5.9, 0.10), 0.2),
                ('via', 'ULPI_STP', (vx, vy, 0.25), 0.2)],
            0: [('via', 'ULPI_STP', (vx, vy, 0.25), 0.2)]}


feasV = []
for i in range(11):
    for j in range(10):
        vx, vy = 76.42 + i * 0.025, 8.98 + j * 0.025
        w, wo = worst(stp_partial(vx, vy))
        feasV.append((round(w, 3), (round(vx, 3), round(vy, 3)), wo))
feasV.sort(reverse=True)
print('STP7 transition candidates:', feasV[:5])
okV = [f for f in feasV if f[0] >= 0]
print(f'feasible V: {len(okV)}')
if okV:
    vx, vy = okV[len(okV) // 2][1]
    print(f'using V = ({vx},{vy})')
    STP7 = {'runs': [{'layer': 2, 'pts': head + [[vx, vy]]},
                     {'layer': 1, 'pts': [[vx, vy], [77.2, 5.9]]}] +
            runs[2:],
            'vias': [[vx, vy]] + ST['vias'][1:]}
    JI = journey_items_dense(STP7, 'ULPI_STP', hw=0.10)
    w, wo = worst(JI)
    print(f'full STP7 gate: {w:+.3f} vs {wo}')
    if w >= 0:
        json.dump(STP7, open('scratch/work/ba/design_stp_south7.json',
                             'w'))
        add_items(JI)
        feasG = []
        for i in range(15):
            for j in range(17):
                gx, gy = 76.95 + i * 0.025, 9.45 + j * 0.025
                w1, wo1 = worst({l: [('via', 'GND', (gx, gy, 0.25), 0.2)]
                                 for l in range(3)})
                if w1 < 0:
                    feasG.append((round(w1, 3), (round(gx, 3),
                                                 round(gy, 3)), wo1))
                    continue
                w2, wo2 = worst({0: [('seg', 'GND',
                                      (77.3, 9.67, gx, gy, 0.10), 0.2)]})
                feasG.append((round(min(w1, w2), 3),
                              (round(gx, 3), round(gy, 3)),
                              wo1 if w1 <= w2 else wo2))
        feasG.sort(reverse=True)
        print('GND via candidates:', feasG[:5])
        okG = [f for f in feasG if f[0] >= 0]
        print(f'feasible G: {len(okG)}')
        if okG:
            print('WINNER G:', okG[len(okG) // 2])
print('=== done ===')
