"""t_ba43: full correct gates for the two C22 finalists in
the joint config (STP7 placed, V=(76.445,9.03)).
A: rot 90 (77.22,9.90) -- pad1 N (77.22,10.38), pad2 S
   (77.22,9.42); hop to (77.90,10.08); GND grid west.
B: rot 180 (77.61,9.9) -- pad1 E (78.09,9.9), pad2 W
   (77.13,9.9); hop to (77.90,10.08); GND grid west.
Pads gated as obstacles (model pad = circumscribed circle,
conservative vs KiCad rects). Score = min(pads, hop, GND)."""
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


def pad_gate(P):
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
    return w, wo


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


def gnd_grid(p2, gx0, gx1, gy0, gy1):
    best = []
    for i in range(int((gx1 - gx0) / 0.025) + 1):
        for j in range(int((gy1 - gy0) / 0.025) + 1):
            gx, gy = gx0 + i * 0.025, gy0 + j * 0.025
            w1, wo1 = worst({l: [('via', 'GND', (gx, gy, 0.25), 0.2)]
                             for l in range(3)})
            if w1 < 0:
                best.append((round(w1, 3), (round(gx, 3), round(gy, 3))))
                continue
            w2, _ = worst({0: [('seg', 'GND', (p2[0], p2[1], gx, gy,
                                              0.10), 0.2)]})
            best.append((round(min(w1, w2), 3),
                         (round(gx, 3), round(gy, 3))))
    best.sort(reverse=True)
    return best


for tag, P1, P2, hop, grid in (
    ('A rot90 (77.22,9.90)',
     ('pad', 'PHY_1V8', (77.22, 10.38, 0.31, 0.28, 0.0), 0.25),
     ('pad', 'GND', (77.22, 9.42, 0.31, 0.28, 0.0), 0.2),
     (77.22, 10.38, 77.90, 10.08), (76.85, 77.10, 9.50, 9.80)),
    ('B rot180 (77.61,9.9)',
     ('pad', 'PHY_1V8', (78.09, 9.90, 0.28, 0.31, 0.0), 0.25),
     ('pad', 'GND', (77.13, 9.90, 0.28, 0.31, 0.0), 0.2),
     (78.09, 9.90, 77.90, 10.08), (76.70, 77.00, 9.55, 9.90)),
):
    w1, wo1 = pad_gate(P1)
    w2, wo2 = pad_gate(P2)
    wh, woh = worst({0: [('seg', 'PHY_1V8', hop + (0.10,), 0.25)]})
    g = gnd_grid((P2[2][0], P2[2][1]), *grid)
    print(f'{tag}: pad1 {w1:+.3f} vs {wo1}; pad2 {w2:+.3f} vs {wo2}; '
          f'hop {wh:+.3f} vs {woh}; GND best {g[0]}')
print('=== done ===')
