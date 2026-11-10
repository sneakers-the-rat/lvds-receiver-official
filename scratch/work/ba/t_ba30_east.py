"""t_ba30: C22 EAST site (78.65,10.55) rot 180 -- pad1 WEST
(78.17,10.55) PHY, pad2 EAST (79.13,10.55) GND. Pad rects
from the board template (hw 0.28, hh 0.31; rot 180 keeps
hw/hh). Gate pads, hop (78.17,10.55)->(77.90,10.08), GND
via grid x[79.45,80.15] y[9.85,10.75] + stub. Pool: exp252
+ t_ba23 STP south placed (its F/B/In2 southern items do
not reach this district, but keep the joint config honest).
Also dump XO F segs x[75.8,78.2] y[9.8,11.9] for the record."""
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
add_items(journey_items_dense(ST, 'ULPI_STP', hw=0.10))
print('joint config placed')

print('--- XO F segs x[75.8,78.2] y[9.8,11.9] ---')
for it in pool[0]:
    if it[1] != 'XO' or it[0] != 'seg':
        continue
    cc = C(it)
    if 75.8 <= cc[0] <= 78.2 and 9.8 <= cc[1] <= 11.9:
        d = it[2]
        print(f'  seg ({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')


def gate_items(items_by_layer, label):
    ps = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                cc = C(o)
                if abs(cc[0] - C(it)[0]) > 4 or abs(cc[1] - C(it)[1]) > 4:
                    continue
                m = item_margin(l, it, [o])
                if m < 0.15:
                    ps.append((round(m, 3), LAYN[l], o[1],
                               (round(C(it)[0], 2), round(C(it)[1], 2)),
                               (round(cc[0], 2), round(cc[1], 2))))
    ps.sort(key=lambda t: t[0])
    n = sum(1 for p in ps if p[0] < 0)
    print(f'{label}: neg {n}, worst 6: {ps[:6]}')
    return n


P1 = ('pad', 'PHY_1V8', (78.17, 10.55, 0.28, 0.31, 0.0), 0.25)
P2 = ('pad', 'GND', (79.13, 10.55, 0.28, 0.31, 0.0), 0.2)
gate_items({0: [P1, P2]}, 'C22 pads (78.65,10.55) r180')
gate_items({0: [('seg', 'PHY_1V8', (78.17, 10.55, 77.90, 10.08, 0.10),
                 0.25)]}, 'pad1 hop')
best = []
for i in range(8):
    for j in range(10):
        vx, vy = 79.45 + i * 0.1, 9.85 + j * 0.1
        gv = gate_items({l: [('via', 'GND', (vx, vy, 0.25), 0.2)]
                         for l in range(3)}, '') if False else None
        # inline gate to keep prints quiet
        w, wo = 9.9, None
        vit = ('via', 'GND', (vx, vy, 0.25), 0.2)
        for l in range(3):
            for o in pool[l]:
                if o[1] == 'GND':
                    continue
                cc = C(o)
                if abs(cc[0] - vx) > 3 or abs(cc[1] - vy) > 3:
                    continue
                m = item_margin(l, vit, [o])
                if m < w:
                    w, wo = m, (LAYN[l], o[1])
        st = ('seg', 'GND', (79.13, 10.55, vx, vy, 0.10), 0.2)
        ws, wos = 9.9, None
        for o in pool[0]:
            if o[1] == 'GND':
                continue
            cc = C(o)
            if abs(cc[0] - (79.13 + vx) / 2) > 3 or \
               abs(cc[1] - (10.55 + vy) / 2) > 3:
                continue
            m = item_margin(0, st, [o])
            if m < ws:
                ws, wos = m, o[1]
        best.append((round(min(w, ws), 3), (vx, vy), round(w, 3), wo,
                     round(ws, 3), wos))
best.sort(reverse=True)
for b in best[:4]:
    print('  GND via cand:', b)
print('=== done ===')
