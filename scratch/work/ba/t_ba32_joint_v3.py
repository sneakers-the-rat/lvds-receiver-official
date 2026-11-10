"""t_ba32: joint design v3, single configuration, full gate.
- STP south: t_ba23 truncated at B pt (76.2,10.5); B descent
  extended to (76.2,9.3); transition via (76.2,9.3); In2
  (76.2,9.3)->(76.9,7.0)->(77.2,5.9); t_ba23 tail kept.
- C22 (77.3,10.15) rot 270: pads, hop (77.3,10.63)->(77.90,
  10.08); GND stub (77.3,9.67)->(76.95,9.6); GND via
  (76.95,9.6).
Saves design_stp_south4.json if STP gates clean."""
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
print(f'ripped {len(rip)} STP southern items')

ST = json.load(open('scratch/work/ba/design_stp_south.json'))
runs = ST['runs']
bpts = [tuple(p) for p in runs[0]['pts']]
i_cut = min(range(len(bpts)),
            key=lambda i: (bpts[i][0] - 76.2) ** 2 + (bpts[i][1] - 10.5) ** 2)
new_runs = [{'layer': 2, 'pts': [list(p) for p in bpts[:i_cut + 1]] +
             [[76.2, 9.3]]},
            {'layer': 1, 'pts': [[76.2, 9.3], [76.9, 7.0], [77.2, 5.9]]}] \
    + runs[2:]
new_vias = [[76.2, 9.3]] + ST['vias'][1:]
ST4 = {'runs': new_runs, 'vias': new_vias}
JI = journey_items_dense(ST4, 'ULPI_STP', hw=0.10)


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


n = gate(JI, 'STP south v3')
if n == 0:
    json.dump(ST4, open('scratch/work/ba/design_stp_south4.json', 'w'))
    add_items(JI)
    print('STP v3 placed; frags', len(fragments('ULPI_STP', BOX)))
gate({0: [('pad', 'PHY_1V8', (77.3, 10.63, 0.31, 0.28, 0.0), 0.25),
          ('pad', 'GND', (77.3, 9.67, 0.31, 0.28, 0.0), 0.2)]},
     'C22 pads (77.3,10.15) r270')
gate({0: [('seg', 'PHY_1V8', (77.3, 10.63, 77.90, 10.08, 0.10), 0.25)]},
     'C22 pad1 hop')
gate({0: [('seg', 'GND', (77.3, 9.67, 76.95, 9.60, 0.10), 0.2)]},
     'C22 GND stub')
gate({l: [('via', 'GND', (76.95, 9.60, 0.25), 0.2)] for l in range(3)},
     'C22 GND via (76.95,9.6)')
print('=== done ===')
