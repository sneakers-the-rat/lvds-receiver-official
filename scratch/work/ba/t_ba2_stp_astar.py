"""t_ba2: STP re-lay search on exp252 with the PHY design placed
(x77.15 loop + design_phy_astar4 journey + tail rip, per t_ba1).
Variants:
  V1 STP A* legs-end (76.10,13.50) -> via (77.0,9.6), layers free
  V2 STP A* legs-end -> via (77.35,7.75) (join further south)
  V3 legs ALSO ripped: dive point (76.065,17.96) -> (77.0,9.6)
  V4 full exit re-plan: F stub+dive+legs ripped too,
     U7.13 pad (76.25,16.4375) F -> (77.0,9.6)
Any FOUND journey is gated exactly (item_margin) and fragment-counted.
"""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
DBOX = (68.0, 90.0, 4.0, 24.0)


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


def gate_exact(items_by_layer, label, thresh=0.30):
    worst = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                m = item_margin(l, it, [o])
                if m < thresh:
                    worst.append((round(m, 3), l, it[1], o[1]))
    worst.sort(key=lambda t: t[0])
    print(f'{label}: {len(worst)} pairs < {thresh}, '
          f'neg {sum(1 for w in worst if w[0] < 0)}, worst 4: {worst[:4]}')
    return worst


pool = load_board_pool(BOARD)

# ---- place PHY design (as t_ba1) ----
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
r = json.load(open('scratch/work/az/design_phy_astar4.json'))
JI2 = journey_items_dense(r, 'PHY_1V8', hw=0.10)
add_items(JI2)
tl = [it for it in pool[0] if it[1] == 'PHY_1V8' and it[0] == 'seg'
      and C(it)[0] < 71.8 and C(it)[1] > 17.4]
rip_items(tl)
print('PHY placed; frags PHY', len(fragments('PHY_1V8', BOX)),
      'STP', len(fragments('ULPI_STP', BOX)))

astar = make_astar(DBOX, 0.05)


def try_variant(name, start, goal, save=None):
    r = astar('ULPI_STP', start, goal, 0.10)
    print(f'{name}:', 'FOUND vias=' + str(r['vias']) if r else 'NONE')
    if r:
        JI = journey_items_dense(r, 'ULPI_STP', hw=0.10)
        gate_exact(JI, f'{name} exact gate')
        add_items(JI)
        print(f'{name}: STP frags now', len(fragments('ULPI_STP', BOX)),
              'PHY frags', len(fragments('PHY_1V8', BOX)))
        if save:
            json.dump(r, open(save, 'w'))
        return r, JI
    return None, None


try_variant('V1 legs-end->(77.0,9.6)', ((2, 1, 0), 76.10, 13.50),
            (2, 77.0, 9.6), 'scratch/work/ba/design_stp_v1.json')
try_variant('V2 legs-end->(77.35,7.75)', ((2, 1, 0), 76.10, 13.50),
            (2, 77.35, 7.75), 'scratch/work/ba/design_stp_v2.json')

# V3: rip the B legs from dive (76.065,17.96) to (76.10,13.50)
legs = []
for it in list(pool[2]):
    if it[1] == 'ULPI_STP' and it[0] == 'seg':
        cc = C(it)
        if 75.8 < cc[0] < 76.4 and 13.4 < cc[1] < 18.0:
            legs.append(it)
print('V3: B legs in dive column:', len(legs))
rip_items(legs)
try_variant('V3 dive->(77.0,9.6)', ((2, 1, 0), 76.065, 17.96),
            (2, 77.0, 9.6), 'scratch/work/ba/design_stp_v3.json')

# V4: rip F stub segs of STP + the dive via; start at U7.13 pad on F
stub = [it for it in list(pool[0])
        if it[1] == 'ULPI_STP' and it[0] == 'seg'
        and 75.9 < C(it)[0] < 76.5 and 16.2 < C(it)[1] < 18.2]
dive = [it for it in pool[0] if it[1] == 'ULPI_STP' and it[0] == 'via'
        and abs(it[2][0] - 76.065) < 0.01 and abs(it[2][1] - 17.96) < 0.01]
print('V4: F stub segs:', len(stub), 'dive via:', len(dive))
rip_items(stub)
rip_items(dive)
try_variant('V4 U7.13pad->(77.0,9.6)', ((0, 1, 2), 76.25, 16.4375),
            (2, 77.0, 9.6), 'scratch/work/ba/design_stp_v4.json')
print('final frags: STP', len(fragments('ULPI_STP', BOX)),
      'PHY', len(fragments('PHY_1V8', BOX)),
      'CK', len(fragments('ULPI_CK', BOX)),
      'XI', len(fragments('XI', BOX)),
      '1V8A', len(fragments('PHY_1V8A', BOX)))
print('=== done ===')
