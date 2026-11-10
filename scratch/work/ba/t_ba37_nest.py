"""t_ba37: the via-nest re-lay, full joint gate.
- +3V3A via (75.62,8.62) r0.4 -> (75.3,8.3); re-lay its
  In2 stubs (staircase start, diag end, south chain top),
  B row east end, B diagonal (straight (75.3,8.3)->
  (71.25,11.12)); F stubs if any end at the old via.
- STP7: transition via (76.55,9.1); B head->(76.55,9.1);
  In2 (76.55,9.1)->(77.2,5.9); t_ba23 tail.
- C22 (77.3,10.15) r270: pads + hop; GND stub to via
  (77.05,9.7); GND via (77.05,9.7).
Gate everything; frags for +3V3A / STP / PHY / GND."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)
print('frags before: +3V3A', len(fragments('+3V3A', BOX)),
      'STP', len(fragments('ULPI_STP', BOX)))

# dump +3V3A items touching (75.62,8.62)
print('--- +3V3A items ending at (75.62,8.62) ---')
for l in range(3):
    for it in pool[l]:
        if it[1] != '+3V3A' or it[0] != 'seg':
            continue
        d = it[2]
        if (abs(d[0] - 75.62) < 0.01 and abs(d[1] - 8.62) < 0.01) or \
           (abs(d[2] - 75.62) < 0.01 and abs(d[3] - 8.62) < 0.01):
            print(f'  {LAYN[l]} seg ({d[0]:.2f},{d[1]:.2f})->'
                  f'({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')
print('--- +3V3A B row items x[73.8,75.7] y[8.45,8.8] ---')
for it in pool[2]:
    if it[1] != '+3V3A' or it[0] != 'seg':
        continue
    cc = C(it)
    if 73.8 <= cc[0] <= 75.7 and 8.45 <= cc[1] <= 8.8:
        d = it[2]
        print(f'  seg ({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},'
              f'{d[3]:.2f}) hw{d[4]}')

# ---- rip STP south (t_ba23 rule) ----
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

# ---- rip the +3V3A nest ----
nest = []
for l in range(3):
    for it in pool[l]:
        if it[1] != '+3V3A':
            continue
        cc = C(it)
        if it[0] == 'via' and abs(cc[0] - 75.62) < 0.01 \
                and abs(cc[1] - 8.62) < 0.01:
            nest.append(it)
        elif it[0] == 'seg':
            d = it[2]
            ends = [(d[0], d[1]), (d[2], d[3])]
            if any(abs(e[0] - 75.62) < 0.01 and abs(e[1] - 8.62) < 0.01
                   for e in ends):
                nest.append(it)
            elif l == 2 and 74.3 <= cc[0] <= 75.7 and 8.45 <= cc[1] <= 8.8:
                nest.append(it)  # B row east end
rip_items(nest)
print(f'nest ripped: {len(nest)} items')

NEW3 = {0: [], 1: [('seg', '+3V3A', (75.3, 8.3, 75.80, 9.20, 0.10), 0.25),
                   ('seg', '+3V3A', (75.50, 9.00, 75.3, 8.3, 0.10), 0.25),
                   ('seg', '+3V3A', (75.55, 8.20, 75.3, 8.3, 0.10), 0.25)],
        2: [('seg', '+3V3A', (75.3, 8.3, 74.3, 8.62, 0.10), 0.25),
            ('seg', '+3V3A', (75.3, 8.3, 71.25, 11.12, 0.10), 0.25)]}
for l in range(3):
    NEW3[l].append(('via', '+3V3A', (75.3, 8.3, 0.40), 0.25))
add_items(NEW3)

ST = json.load(open('scratch/work/ba/design_stp_south.json'))
runs = ST['runs']
bpts = [tuple(p) for p in runs[0]['pts']]
i_cut = min(range(len(bpts)),
            key=lambda i: (bpts[i][0] - 76.2) ** 2 + (bpts[i][1] - 10.5) ** 2)
head = [list(p) for p in bpts[:i_cut + 1]]
STP7 = {'runs': [{'layer': 2, 'pts': head + [[76.55, 9.1]]},
                 {'layer': 1, 'pts': [[76.55, 9.1], [77.2, 5.9]]}] +
        runs[2:],
        'vias': [[76.55, 9.1]] + ST['vias'][1:]}
JI7 = journey_items_dense(STP7, 'ULPI_STP', hw=0.10)
add_items(JI7)
C22I = {0: [('pad', 'PHY_1V8', (77.3, 10.63, 0.31, 0.28, 0.0), 0.25),
            ('pad', 'GND', (77.3, 9.67, 0.31, 0.28, 0.0), 0.2),
            ('seg', 'PHY_1V8', (77.3, 10.63, 77.90, 10.08, 0.10), 0.25),
            ('seg', 'GND', (77.3, 9.67, 77.05, 9.70, 0.10), 0.2)]}
GV = {l: [('via', 'GND', (77.05, 9.70, 0.25), 0.2)] for l in range(3)}


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


tot = 0
tot += gate(NEW3, '+3V3A nest re-lay')
tot += gate(JI7, 'STP7')
tot += gate(C22I, 'C22 pads+hop+stub')
tot += gate(GV, 'GND via (77.05,9.7)')
print('frags after: +3V3A', len(fragments('+3V3A', BOX)),
      'STP', len(fragments('ULPI_STP', BOX)),
      'PHY', len(fragments('PHY_1V8', BOX)))
if tot == 0:
    json.dump(STP7, open('scratch/work/ba/design_stp_south7.json', 'w'))
    print('ALL CLEAN -- designs saved')
print('=== done ===')
