"""t_ba39: joint micro-optimization of (STP7 transition
via V, GND via G). For each V in the t_ba38 feasible set
(recomputed), place full STP7, grid G over x[76.9,77.35]
y[9.4,9.9] (0.025), score = min(V margin, G via margin,
G stub margin). Save the winning STP7 + report G."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool0 = load_board_pool(BOARD)
RIP = []
for l in range(3):
    for it in pool0[l]:
        if it[1] != 'ULPI_STP' or it[0] not in ('seg', 'via'):
            continue
        cc = C(it)
        if 75.5 <= cc[0] <= 78.5 and 7.0 <= cc[1] <= 14.0:
            RIP.append(it)
        elif 0.5 < cc[1] < 7.5 and cc[0] > 72.0:
            RIP.append(it)
ST = json.load(open('scratch/work/ba/design_stp_south.json'))
runs = ST['runs']
bpts = [tuple(p) for p in runs[0]['pts']]
i_cut = min(range(len(bpts)),
            key=lambda i: (bpts[i][0] - 76.2) ** 2 + (bpts[i][1] - 10.5) ** 2)
head = [list(p) for p in bpts[:i_cut + 1]]


def worst(pool, items_by_layer):
    w, wo = 9.9, None
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                cc, ci = C(o), C(it)
                if abs(cc[0] - ci[0]) > 4 or abs(cc[1] - ci[1]) > 4:
                    continue
                m = item_margin(l, it, [o])
                if m < w:
                    w, wo = m, (LAYN[l], o[1])
    return w, wo


# feasible V set (partial-journey gate), base pool
pool = load_board_pool(BOARD)
rip_items(list(RIP))
feasV = []
for i in range(11):
    for j in range(10):
        vx, vy = 76.42 + i * 0.025, 8.98 + j * 0.025
        items = {2: [('seg', 'ULPI_STP', (76.2, 10.5, vx, vy, 0.10), 0.2),
                     ('via', 'ULPI_STP', (vx, vy, 0.25), 0.2)],
                 1: [('seg', 'ULPI_STP', (vx, vy, 77.2, 5.9, 0.10), 0.2),
                     ('via', 'ULPI_STP', (vx, vy, 0.25), 0.2)],
                 0: [('via', 'ULPI_STP', (vx, vy, 0.25), 0.2)]}
        w, _ = worst(pool, items)
        if w >= 0:
            feasV.append((round(vx, 3), round(vy, 3)))
print(f'feasible V set: {len(feasV)} pts')

results = []
for (vx, vy) in feasV:
    pool = load_board_pool(BOARD)
    rip_items(list(RIP))
    STP7 = {'runs': [{'layer': 2, 'pts': head + [[vx, vy]]},
                     {'layer': 1, 'pts': [[vx, vy], [77.2, 5.9]]}] +
            runs[2:],
            'vias': [[vx, vy]] + ST['vias'][1:]}
    JI = journey_items_dense(STP7, 'ULPI_STP', hw=0.10)
    w_full, _ = worst(pool, JI)
    if w_full < 0:
        continue
    add_items(JI)
    bestG = (-9, None)
    for i in range(19):
        for j in range(21):
            gx, gy = 76.9 + i * 0.025, 9.4 + j * 0.025
            w1, _ = worst(pool, {l: [('via', 'GND', (gx, gy, 0.25), 0.2)]
                                 for l in range(3)})
            if w1 <= bestG[0]:
                continue
            w2, _ = worst(pool, {0: [('seg', 'GND',
                                      (77.3, 9.67, gx, gy, 0.10), 0.2)]})
            s = min(w1, w2)
            if s > bestG[0]:
                bestG = (s, (round(gx, 3), round(gy, 3)))
    results.append((round(min(w_full, bestG[0]), 3), (vx, vy), bestG))
    print(f'  V=({vx},{vy}): full {w_full:+.3f}, best G {bestG}')
results.sort(reverse=True)
print('BEST:', results[0] if results else None)
if results and results[0][0] >= 0:
    vx, vy = results[0][1]
    STP7 = {'runs': [{'layer': 2, 'pts': head + [[vx, vy]]},
                     {'layer': 1, 'pts': [[vx, vy], [77.2, 5.9]]}] +
            runs[2:],
            'vias': [[vx, vy]] + ST['vias'][1:]}
    json.dump(STP7, open('scratch/work/ba/design_stp_south7.json', 'w'))
    json.dump({'gnd_via': results[0][2][1]},
              open('scratch/work/ba/design_gnd_tie.json', 'w'))
    print('saved STP7 + GND tie')
print('=== done ===')
