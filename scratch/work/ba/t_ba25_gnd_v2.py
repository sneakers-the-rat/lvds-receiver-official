"""t_ba25: GND tie v2 in the TRUE joint configuration: exp252
pool + t_ba23 STP southern re-plan placed (southern chain
ripped per its rule). For C22 sites (77.15,9.55) rot 270,
(77.3,9.5) rot 270, (77.5,9.7) rot 270: gate pad1 hop to the
PHY via point (77.90,10.08); scan GND vias on a 0.15 grid
x[76.2,78.4] y[8.2,10.3]; gate the GND track to the best via."""
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
print(f'STP south placed (ripped {len(rip)}); frags '
      f'{len(fragments("ULPI_STP", BOX))}')


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
            w, wo = m, o[1]
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


for (cx, cy) in [(77.15, 9.55), (77.3, 9.5), (77.5, 9.7)]:
    p1 = (cx, cy + 0.48)
    p2 = (cx, cy - 0.48)
    g, w = gate_track(0, 'PHY_1V8', p1[0], p1[1], 77.90, 10.08)
    cands = []
    for i in range(15):
        for j in range(15):
            vx, vy = 76.2 + i * 0.15, 8.2 + j * 0.15
            gv, wo = gate_via(vx, vy)
            cands.append((round(gv, 3), (round(vx, 2), round(vy, 2)), wo))
    cands.sort(reverse=True)
    print(f'site ({cx},{cy}) r270: pad1 {p1} hop {g:+.3f} vs {w}')
    for c in cands[:3]:
        vx, vy = c[1]
        gt, wt = gate_track(0, 'GND', p2[0], p2[1], vx, vy)
        print(f'   GND via {c[1]} gate {c[0]:+.3f} (worst {c[2]}); '
              f'track from pad2 {p2}: {gt:+.3f} vs {wt}')
print('=== done ===')
