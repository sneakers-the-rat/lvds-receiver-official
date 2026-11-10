"""t_ba1: re-run az37's PHY_1V8 model solution on the FAITHFUL exp252
pool (notch at banked v4 (75.27,10.33), not modelled v2).
Steps: baseline frags; gate PHY journey+loop vs pool WITH STP chain
present (conflict census); rip STP B chain; rip PHY B loop; add
x77.15 loop; add design_phy_astar4 journey; gate; rip PHY F tail;
final fragment counts."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)


def seg(net, x1, y1, x2, y2, hw=0.10, clr=0.2):
    return ('seg', net, (x1, y1, x2, y2, hw), clr)


def via(net, x, y, r=0.25, clr=0.2):
    return ('via', net, (x, y, r), clr)


def gate_items(items_by_layer, label, thresh=0.30):
    worst = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                m = item_margin(l, it, [o])
                if m < thresh:
                    worst.append((round(m, 3), l, it[1], o[1],
                                  (round(C(it)[0], 2), round(C(it)[1], 2)),
                                  (round(C(o)[0], 2), round(C(o)[1], 2))))
    worst.sort(key=lambda t: t[0])
    print(f'{label}: {len(worst)} pairs < {thresh}; worst 8:')
    for w in worst[:8]:
        print('   ', w)
    return worst


def rip_pair(net, l, a, b):
    out = []
    for it in pool[l]:
        if it[1] != net or it[0] != 'seg':
            continue
        d = it[2]
        if (abs(d[0] - a[0]) < 0.01 and abs(d[1] - a[1]) < 0.01
                and abs(d[2] - b[0]) < 0.01 and abs(d[3] - b[1]) < 0.01) or \
           (abs(d[0] - b[0]) < 0.01 and abs(d[1] - b[1]) < 0.01
                and abs(d[2] - a[0]) < 0.01 and abs(d[3] - a[1]) < 0.01):
            out.append(it)
    if out:
        rip_items(out)
    return len(out)


pool = load_board_pool(BOARD)
print('baseline frags: PHY', len(fragments('PHY_1V8', BOX)),
      'STP', len(fragments('ULPI_STP', BOX)),
      'CK', len(fragments('ULPI_CK', BOX)),
      'XI', len(fragments('XI', BOX)),
      '1V8A', len(fragments('PHY_1V8A', BOX)),
      'XO', len(fragments('XO', BOX)))

# --- the design under test ---
r = json.load(open('scratch/work/az/design_phy_astar4.json'))
JI2 = journey_items_dense(r, 'PHY_1V8', hw=0.10)
N4 = {0: [], 1: [], 2: [seg('PHY_1V8', 77.90, 10.08, 77.50, 10.25, 0.15, 0.25),
                       seg('PHY_1V8', 77.50, 10.25, 77.28, 10.80, 0.10, 0.25),
                       seg('PHY_1V8', 77.28, 10.80, 77.15, 11.30, 0.10, 0.25),
                       seg('PHY_1V8', 77.15, 11.30, 77.15, 13.00, 0.15, 0.25),
                       seg('PHY_1V8', 77.15, 13.00, 77.15, 15.10, 0.15, 0.25),
                       seg('PHY_1V8', 77.15, 15.10, 77.80, 16.20, 0.15, 0.25)]}

print('--- gate vs pool WITH STP chain present (conflict census) ---')
gate_items(JI2, 'PHY journey vs exp252 full pool', 0.05)
gate_items(N4, 'PHY x77.15 loop vs exp252 full pool', 0.05)

# --- az37 configuration: rip STP chain + PHY loop, add design ---
ch = chain_segs(pool, 'ULPI_STP', 2, (76.10, 13.50), (77.0, 9.6))
print('STP chain segs found:', len(ch))
for it in ch:
    d = it[2]
    print('   STP B seg', (round(d[0], 3), round(d[1], 3)),
          '->', (round(d[2], 3), round(d[3], 3)), 'hw', d[4])
rip_items(ch)
n = 0
n += rip_pair('PHY_1V8', 2, (77.90, 10.08), (77.45, 10.10))
n += rip_pair('PHY_1V8', 2, (77.45, 10.10), (76.95, 11.05))
n += rip_pair('PHY_1V8', 2, (76.95, 11.05), (76.95, 14.988))
n += rip_pair('PHY_1V8', 2, (76.95, 14.988), (77.80, 16.20))
print('PHY loop pair-ripped:', n)
add_items(N4)
w1 = gate_items(JI2, 'PHY journey gate (STP ripped, exp252)', 0.30)
add_items(JI2)
w2 = gate_items(N4, 'PHY loop gate (post-add, exp252)', 0.30)
tl = [it for it in pool[0] if it[1] == 'PHY_1V8' and it[0] == 'seg'
      and C(it)[0] < 71.8 and C(it)[1] > 17.4]
rip_items(tl)
print('PHY tail ripped:', len(tl))
print('final frags: PHY', len(fragments('PHY_1V8', BOX)),
      'STP', len(fragments('ULPI_STP', BOX)),
      'CK', len(fragments('ULPI_CK', BOX)),
      'XI', len(fragments('XI', BOX)),
      '1V8A', len(fragments('PHY_1V8A', BOX)),
      'XO', len(fragments('XO', BOX)))
neg = [w for w in w1 + w2 if w[0] < 0.0]
print('negative-margin pairs in design:', len(neg))
print('=== done ===')
