"""t_ba42b: CORRECT full gate for C22 at (77.0,9.85) rot 90
(pad1 PHY (77.0,10.33), pad2 GND (77.0,9.37)) in the joint
config (exp252 pool + STP7 placed, V=(76.445,9.03)).
Pads gated as OBSTACLES (pool items as subjects -- the
pad-subject 9.9 sentinel voided earlier pad gates). Hop,
GND via micro-grid x[76.8,77.05] y[9.5,9.8], GND stub."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
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
ST7 = json.load(open('scratch/work/ba/design_stp_south7.json'))
add_items(journey_items_dense(ST7, 'ULPI_STP', hw=0.10))
print('STP7 placed (V =', ST7['vias'][0], ')')

P1 = ('pad', 'PHY_1V8', (77.0, 10.33, 0.31, 0.28, 0.0), 0.25)
P2 = ('pad', 'GND', (77.0, 9.37, 0.31, 0.28, 0.0), 0.2)
for P, nm in ((P1, 'pad1 PHY'), (P2, 'pad2 GND')):
    w, wo = 9.9, None
    for o in pool[0]:
        if o[1] == P[1]:
            continue
        cc = C(o)
        if abs(cc[0] - P[2][0]) > 3 or abs(cc[1] - P[2][1]) > 3:
            continue
        m = item_margin(0, o, [P])
        if m < w:
            w, wo = m, (o[1], (round(cc[0], 2), round(cc[1], 2)))
    print(f'{nm}: worst margin {w:+.3f} vs {wo}')


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


w, wo = worst({0: [('seg', 'PHY_1V8', (77.0, 10.33, 77.90, 10.08, 0.10),
                    0.25)]})
print(f'hop (77.0,10.33)->(77.90,10.08): {w:+.3f} vs {wo}')
best = []
for i in range(11):
    for j in range(13):
        gx, gy = 76.8 + i * 0.025, 9.5 + j * 0.025
        w1, wo1 = worst({l: [('via', 'GND', (gx, gy, 0.25), 0.2)]
                         for l in range(3)})
        if w1 < 0:
            best.append((round(w1, 3), (round(gx, 3), round(gy, 3)), wo1))
            continue
        w2, wo2 = worst({0: [('seg', 'GND', (77.0, 9.37, gx, gy, 0.10),
                              0.2)]})
        best.append((round(min(w1, w2), 3), (round(gx, 3), round(gy, 3)),
                     wo1 if w1 <= w2 else wo2))
best.sort(reverse=True)
print('GND via candidates:', best[:5])
ok = [b for b in best if b[0] >= 0]
print(f'feasible GND vias: {len(ok)}')
if ok:
    json.dump({'gnd_via': list(ok[len(ok) // 2][1])},
              open('scratch/work/ba/design_gnd_tie.json', 'w'))
    print('saved GND via', ok[len(ok) // 2][1])
print('=== done ===')
