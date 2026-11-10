"""t_ba28: GND tie v3 -- via in the pocket at (77.66,9.55),
north of D0's staircase corner (77.88,9.12), east of STP's
transition, south of PHY's stub. Joint config: exp252 pool +
t_ba23 STP south placed. Gate: C22 pad1 hop, GND stub
(77.5,9.22)->(77.66,9.55), GND via (77.66,9.55); small grid
around the pocket for the best point."""
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


def gate_track(l, net, x1, y1, x2, y2, hw=0.10):
    it = ('seg', net, (x1, y1, x2, y2, hw),
          0.25 if net == 'PHY_1V8' else 0.2)
    w, wo = 9.9, None
    for o in pool[l]:
        if o[1] == net:
            continue
        cc = C(o)
        if abs(cc[0] - (x1 + x2) / 2) > 4 or abs(cc[1] - (y1 + y2) / 2) > 4:
            continue
        m = item_margin(l, it, [o])
        if m < w:
            w, wo = m, (o[1], (round(cc[0], 2), round(cc[1], 2)))
    return w, wo


def gate_via(x, y, net='GND'):
    it = ('via', net, (x, y, 0.25), 0.2)
    w, wo = 9.9, None
    for l in range(3):
        for o in pool[l]:
            if o[1] == net:
                continue
            cc = C(o)
            if abs(cc[0] - x) > 3 or abs(cc[1] - y) > 3:
                continue
            m = item_margin(l, it, [o])
            if m < w:
                w, wo = m, (LAYN[l], o[1],
                            (round(cc[0], 2), round(cc[1], 2)))
    return w, wo


g, w = gate_track(0, 'PHY_1V8', 77.50, 10.18, 77.90, 10.08)
print(f'pad1 hop: {g:+.3f} vs {w}')
best = []
for i in range(7):
    for j in range(7):
        vx, vy = 77.45 + i * 0.07, 9.40 + j * 0.07
        gv, wo = gate_via(vx, vy)
        gt, wt = gate_track(0, 'GND', 77.5, 9.22, vx, vy)
        best.append((round(min(gv, gt), 3), (round(vx, 2), round(vy, 2)),
                     round(gv, 3), wo, round(gt, 3), wt))
best.sort(reverse=True)
for b in best[:5]:
    print('  via cand:', b)
print('=== done ===')
