"""t_ba29: joint design v2.
- STP south: t_ba23 design with hand surgery -- B descent
  extended at x76.2 to (76.2,8.9), transition via moved
  (76.75,9.45)->(76.2,8.9), In2 run replaced by the straight
  diagonal (76.2,8.9)->(77.2,5.9). Full gate.
- C22 at (76.9,10.15) rot 270 with REAL pad items (dims from
  the board's C22 pads): gate pads vs pool, pad1 hop to
  (77.90,10.08), GND stub (76.9,9.67)->(76.85,9.7), GND via
  (76.85,9.7)."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)

for it in pool[0]:
    if it[0] == 'pad' and it[1] in ('PHY_1V8', 'GND'):
        cc = C(it)
        if abs(cc[0] - 72.02) < 0.1 or abs(cc[0] - 72.98) < 0.1:
            print('C22 pad item:', it)

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
# surgery on runs: runs[0] = B descent, runs[1] = In2
runs = ST['runs']
bpts = [tuple(p) for p in runs[0]['pts']]
# truncate B run at the pt nearest (76.2,10.5)
i_cut = min(range(len(bpts)),
            key=lambda i: (bpts[i][0] - 76.2) ** 2 + (bpts[i][1] - 10.5) ** 2)
new_b = bpts[:i_cut + 1] + [(76.2, 8.9)]
runs[0]['pts'] = [list(p) for p in new_b]
runs[1]['pts'] = [[76.2, 8.9], [77.2, 5.9]]
ST['vias'][0] = [76.2, 8.9]
print(f'STP surgery: B run {len(bpts)}->{len(new_b)} pts, vias {ST["vias"]}')
JI = journey_items_dense(ST, 'ULPI_STP', hw=0.10)
pairs = []
for l in range(3):
    for it in JI.get(l, []):
        for o in pool[l]:
            if o[1] == 'ULPI_STP':
                continue
            m = item_margin(l, it, [o])
            if m < 0.1:
                pairs.append((round(m, 3), LAYN[l], o[1],
                              (round(C(it)[0], 2), round(C(it)[1], 2)),
                              (round(C(o)[0], 2), round(C(o)[1], 2))))
pairs.sort(key=lambda t: t[0])
neg = sum(1 for p in pairs if p[0] < 0)
print(f'STP adjusted gate: neg {neg}, worst 6: {pairs[:6]}')
if neg == 0:
    json.dump(ST, open('scratch/work/ba/design_stp_south3.json', 'w'))
    add_items(JI)
    print('STP adjusted placed; frags', len(fragments('ULPI_STP', BOX)))


def gate_items(items_by_layer, label):
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


# C22 pads at rot 270: pad dims from a 0402 in the pool --
# reuse the exact pad tuple shape of C22's current pads.
# Current pads (from the print above) carry (x, y, hw, hh).
# At rot 270 pad1 (PHY) is NORTH: (76.9, 10.15+0.48);
# pad2 (GND) SOUTH: (76.9, 10.15-0.48). hw/hh swap.
import copy
tmpl = None
for it in pool[0]:
    if it[0] == 'pad' and it[1] == 'PHY_1V8':
        cc = C(it)
        if abs(cc[0] - 72.02) < 0.1:
            tmpl = it
            break
print('pad template:', tmpl)
d = tmpl[2]
hw, hh = d[2], d[3]
P1 = ('pad', 'PHY_1V8', (76.9, 10.63, hh, hw), tmpl[3])
P2 = ('pad', 'GND', (76.9, 9.67, hh, hw), tmpl[3])
gate_items({0: [P1, P2]}, 'C22 pads at (76.9,10.15) r270')
HOP = {0: [('seg', 'PHY_1V8', (76.9, 10.63, 77.90, 10.08, 0.10), 0.25)]}
gate_items(HOP, 'C22 pad1 hop')
GSTUB = {0: [('seg', 'GND', (76.9, 9.67, 76.85, 9.70, 0.10), 0.2)]}
gate_items(GSTUB, 'C22 GND stub')
GVIA = {l: [('via', 'GND', (76.85, 9.70, 0.25), 0.2)] for l in range(3)}
gate_items(GVIA, 'C22 GND via (76.85,9.70)')
print('=== done ===')
