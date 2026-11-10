"""t_ba35: STP5 -- transition via in the SW pocket. Grid the
transition via V over x[76.5,76.85] y[8.55,8.95] (0.05):
items = B descent extension (76.2,10.5)->V, In2 V->(77.2,
5.9), via V; plus t_ba23 tail runs for the full-journey
gate at the best V. Then GND via grid x[76.9,77.2]
y[9.55,9.85] with the winner placed. C22 (77.3,10.15) r270
pads/hop/stub gated throughout."""
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


def worst(items_by_layer):
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


def stp_items(vx, vy, full=True):
    r = [{'layer': 2, 'pts': head + [[vx, vy]]},
         {'layer': 1, 'pts': [[vx, vy], [77.2, 5.9]]}]
    if full:
        r = r + runs[2:]
    vias = [[vx, vy]] + (ST['vias'][1:] if full else [])
    return journey_items_dense({'runs': r, 'vias': vias},
                               'ULPI_STP', hw=0.10)


cands = []
for i in range(8):
    for j in range(9):
        vx, vy = 76.5 + i * 0.05, 8.55 + j * 0.05
        w, wo = worst(stp_items(vx, vy, full=False))
        cands.append((round(w, 3), (round(vx, 2), round(vy, 2)), wo))
cands.sort(reverse=True)
print('transition-via candidates (partial journey):')
for c in cands[:6]:
    print('  ', c)
ok = [c for c in cands if c[0] >= 0]
if ok:
    vx, vy = ok[0][1]
    JI = stp_items(vx, vy, full=True)
    w, wo = worst(JI)
    print(f'full STP5 at V=({vx},{vy}): worst {w:+.3f} vs {wo}')
    if w >= 0:
        ST5 = {'runs': [{'layer': 2, 'pts': head + [[vx, vy]]},
                        {'layer': 1, 'pts': [[vx, vy], [77.2, 5.9]]}] +
               runs[2:],
               'vias': [[vx, vy]] + ST['vias'][1:]}
        json.dump(ST5, open('scratch/work/ba/design_stp_south5.json', 'w'))
        add_items(JI)
        print('STP5 placed; frags', len(fragments('ULPI_STP', BOX)))
        best = []
        for i in range(7):
            for j in range(7):
                gx, gy = 76.9 + i * 0.05, 9.55 + j * 0.05
                w1, _ = worst({l: [('via', 'GND', (gx, gy, 0.25), 0.2)]
                               for l in range(3)})
                if w1 < 0:
                    continue
                w2, _ = worst({0: [('seg', 'GND',
                                    (77.3, 9.67, gx, gy, 0.10), 0.2)]})
                if w2 < 0:
                    continue
                best.append((round(min(w1, w2), 3),
                             (round(gx, 2), round(gy, 2))))
        best.sort(reverse=True)
        print('GND via candidates with STP5 placed:', best[:5])
        w3, wo3 = worst({0: [('seg', 'PHY_1V8',
                              (77.3, 10.63, 77.90, 10.08, 0.10), 0.25)]})
        print(f'pad1 hop re-gate: {w3:+.3f} vs {wo3}')
print('=== done ===')
