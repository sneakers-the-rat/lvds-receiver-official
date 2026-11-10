"""t_ba14: PHY_1V8A re-plan entirely on In2 between the two
through vias that already exist: notch via (75.27,10.33) ->
tail via (71.48,15.38). Config: exp252 + PHY design (ba shift,
design_phy_ba.json) + tuned STP (design_stp_tuned.json) + ALL
1V8A routed copper ripped. A* start = notch point (all layers),
goal = tail-via point on In2; fallback goal B; fallback hand
polyline gated exactly."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
DBOX = (68.0, 90.0, 4.0, 24.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}


def seg(net, x1, y1, x2, y2, hw=0.10, clr=0.2):
    return ('seg', net, (x1, y1, x2, y2, hw), clr)


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


def gate(JI, net):
    pairs = []
    for l in range(3):
        for it in JI.get(l, []):
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < 0.1:
                    pairs.append((round(m, 3), LAYN[l], o[1],
                                  (round(C(it)[0], 2), round(C(it)[1], 2)),
                                  (round(C(o)[0], 2), round(C(o)[1], 2))))
    pairs.sort(key=lambda t: t[0])
    return pairs


pool = load_board_pool(BOARD)
# rip all 1V8A routed copper
v1 = [it for l in range(3) for it in pool[l]
      if it[1] == 'PHY_1V8A' and it[0] in ('seg', 'via')]
rip_items(v1)
# STP chain rip + PHY design (ba variant)
ch = chain_segs(pool, 'ULPI_STP', 2, (76.10, 13.50), (77.0, 9.6))
rip_items(ch)
n = 0
n += rip_pair('PHY_1V8', 2, (77.90, 10.08), (77.45, 10.10))
n += rip_pair('PHY_1V8', 2, (77.45, 10.10), (76.95, 11.05))
n += rip_pair('PHY_1V8', 2, (76.95, 11.05), (76.95, 14.988))
n += rip_pair('PHY_1V8', 2, (76.95, 14.988), (77.80, 16.20))
N4 = {0: [], 1: [], 2: [seg('PHY_1V8', 77.90, 10.08, 77.50, 10.25, 0.15, 0.25),
                       seg('PHY_1V8', 77.50, 10.25, 77.28, 10.80, 0.10, 0.25),
                       seg('PHY_1V8', 77.28, 10.80, 77.15, 11.30, 0.10, 0.25),
                       seg('PHY_1V8', 77.15, 11.30, 77.15, 13.00, 0.15, 0.25),
                       seg('PHY_1V8', 77.15, 13.00, 77.15, 15.10, 0.15, 0.25),
                       seg('PHY_1V8', 77.15, 15.10, 77.80, 16.20, 0.15, 0.25)]}
add_items(N4)
r = json.load(open('scratch/work/ba/design_phy_ba.json'))
add_items(journey_items_dense(r, 'PHY_1V8', hw=0.10))
tl = [it for it in pool[0] if it[1] == 'PHY_1V8' and it[0] == 'seg'
      and C(it)[0] < 71.8 and C(it)[1] > 17.4]
rip_items(tl)
# tuned STP
ST = json.load(open('scratch/work/ba/design_stp_tuned.json'))
add_items(journey_items_dense(ST, 'ULPI_STP', hw=0.10))
print(f'config: PHY frags {len(fragments("PHY_1V8", BOX))}, STP frags '
      f'{len(fragments("ULPI_STP", BOX))}, 1V8A ripped {len(v1)} items')

astar = make_astar(DBOX, 0.05)
win = None
for label, goal in [('In2 goal', (1, 71.48, 15.38)),
                    ('B goal', (2, 71.48, 15.38))]:
    rr = astar('PHY_1V8A', ((2, 1, 0), 75.27, 10.33), goal, 0.10)
    print(f'1V8A notch->tail {label}:',
          'FOUND vias=' + str(rr['vias']) if rr else 'NONE')
    if rr:
        JI = journey_items_dense(rr, 'PHY_1V8A', hw=0.10)
        pairs = gate(JI, 'PHY_1V8A')
        neg = sum(1 for p in pairs if p[0] < 0)
        print(f'   gate: neg {neg}, worst 6: {pairs[:6]}')
        if neg == 0:
            win = rr
            json.dump(rr, open('scratch/work/ba/design_1v8a_in2.json', 'w'))
            add_items(JI)
            break
if not win:
    HAND = [(75.27, 10.33), (74.60, 9.70), (73.40, 9.32), (72.60, 9.30),
            (71.95, 9.38), (71.58, 10.20), (71.55, 12.50), (71.44, 13.20),
            (71.48, 15.38)]
    design = {'vias': [], 'runs': [{'layer': 1,
                                    'pts': [list(p) for p in HAND]}]}
    JI = journey_items_dense(design, 'PHY_1V8A', hw=0.10)
    pairs = gate(JI, 'PHY_1V8A')
    neg = sum(1 for p in pairs if p[0] < 0)
    print(f'hand polyline gate: neg {neg}, worst 8: {pairs[:8]}')
    if neg == 0:
        json.dump(design, open('scratch/work/ba/design_1v8a_in2.json', 'w'))
        add_items(JI)
        print('hand polyline SAVED')
print('final frags: PHY', len(fragments('PHY_1V8', BOX)),
      'STP', len(fragments('ULPI_STP', BOX)),
      '1V8A', len(fragments('PHY_1V8A', BOX)),
      'CK', len(fragments('ULPI_CK', BOX)),
      'XI', len(fragments('XI', BOX)),
      'XO', len(fragments('XO', BOX)))
print('=== done ===')
