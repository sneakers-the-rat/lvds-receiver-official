"""t_az25: PHY via sequential A*.
Pool: faithful + STP mega-rip (v11 box) + PHY loop re-lay (x77.15).
NO STP re-lay yet. A* PHY C22.1 -> (77.8,16.2) B; print journey.
Then add PHY journey; A* STP re-lay (76.1,13.5) B -> (77,9.6) B
(multi-layer allowed); print + gate both journeys.
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)


def seg(net, x1, y1, x2, y2, hw=0.10, clr=0.2):
    return ('seg', net, (x1, y1, x2, y2, hw), clr)


def gate_items(items_by_layer, label, thresh=0.30):
    worst = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                m = item_margin(l, it, [o])
                if m < thresh:
                    worst.append((round(m, 3), l, it, o))
    worst.sort(key=lambda t: t[0])
    print(f'{label}: {len(worst)} pairs < {thresh}; worst 6:')
    for w in worst[:6]:
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
mg = [it for it in pool[2] if it[1] == 'ULPI_STP' and it[0] == 'seg'
      and 75.8 < C(it)[0] < 77.05 and 9.45 < C(it)[1] < 13.45]
rip_items(mg)
print('STP mega-ripped:', len(mg))
n = 0
n += rip_pair('PHY_1V8', 2, (77.90, 10.08), (77.45, 10.10))
n += rip_pair('PHY_1V8', 2, (77.45, 10.10), (76.95, 11.05))
n += rip_pair('PHY_1V8', 2, (76.95, 11.05), (76.95, 14.988))
n += rip_pair('PHY_1V8', 2, (76.95, 14.988), (77.80, 16.20))
print('PHY loop pair-ripped:', n)
N4 = {0: [], 1: [], 2: [seg('PHY_1V8', 77.90, 10.08, 77.50, 10.25, 0.15, 0.25),
                       seg('PHY_1V8', 77.50, 10.25, 77.28, 10.80, 0.10, 0.25),
                       seg('PHY_1V8', 77.28, 10.80, 77.15, 11.30, 0.10, 0.25),
                       seg('PHY_1V8', 77.15, 11.30, 77.15, 15.10, 0.15, 0.25),
                       seg('PHY_1V8', 77.15, 15.10, 77.80, 16.20, 0.15, 0.25)]}
add_items(N4)
gate_items(N4, 'PHY loop gate')
print('PHY fragments:', len(fragments('PHY_1V8', BOX)))

astar = make_astar((70.0, 88.0, 8.0, 23.0), 0.05)
r = astar('PHY_1V8', ((0,), 72.02, 18.0), (2, 77.8, 16.2), 0.10)
print('PHY A*:', 'FOUND vias=' + str(r['vias']) if r else 'none')
if r:
    for rn in r['runs']:
        print(f"  L{rn['layer']} pts: {rn['pts']}")
    gate_items(journey_items_dense(r, 'PHY_1V8', hw=0.10),
               'PHY journey gate')
    add_items(journey_items_dense(r, 'PHY_1V8', hw=0.10))
    print('PHY fragments after journey:',
          len(fragments('PHY_1V8', BOX)))
    r2 = astar('ULPI_STP', ((2,), 76.1, 13.5), (2, 77.0, 9.6), 0.10)
    print('STP re-lay A*:', 'FOUND vias=' + str(r2['vias']) if r2
          else 'none')
    if r2:
        for rn in r2['runs']:
            print(f"  L{rn['layer']} pts: {rn['pts']}")
        gate_items(journey_items_dense(r2, 'ULPI_STP', hw=0.10),
                   'STP re-lay gate')
        add_items(journey_items_dense(r2, 'ULPI_STP', hw=0.10))
        print('STP fragments after re-lay:',
              len(fragments('ULPI_STP', BOX)))
print('=== done ===')

# --- appended: STP hand re-lay gate on the PHY-added pool ---
N3 = {0: [], 1: [], 2: [
    seg('ULPI_STP', 76.10, 13.50, 75.45, 13.25),
    seg('ULPI_STP', 75.45, 13.25, 75.45, 12.10),
    seg('ULPI_STP', 75.45, 12.10, 75.75, 11.88),
    seg('ULPI_STP', 75.75, 11.88, 76.00, 11.85),
    seg('ULPI_STP', 76.00, 11.85, 76.30, 11.55),
    seg('ULPI_STP', 76.30, 11.55, 76.75, 10.50),
    seg('ULPI_STP', 76.75, 10.50, 76.90, 9.70),
    seg('ULPI_STP', 76.90, 9.70, 77.00, 9.60)]}
gate_items(N3, 'STP hand re-lay gate (post-PHY)')
add_items(N3)
print('STP fragments after hand re-lay:',
      len(fragments('ULPI_STP', BOX)))
# rip PHY tail segs and recount
tl = [it for it in pool[0] if it[1] == 'PHY_1V8' and it[0] == 'seg'
      and C(it)[0] < 71.8 and C(it)[1] > 17.4]
rip_items(tl)
print('PHY tail segs ripped:', len(tl))
print('PHY fragments final:', len(fragments('PHY_1V8', BOX)))
print('=== done2 ===')

# --- appended2: STP re-lay v3 (west descent) gate ---
def path_items(net, layer, pts, hw=0.10, clr=0.2):
    out = []
    for i in range(len(pts) - 1):
        out.append(seg(net, pts[i][0], pts[i][1], pts[i + 1][0],
                       pts[i + 1][1], hw, clr))
    return {layer: out}

STP3 = path_items('ULPI_STP', 2, [(74.55, 14.75), (73.55, 14.0),
                                  (73.7, 13.4), (74.45, 12.7),
                                  (74.85, 12.1), (75.7, 11.85),
                                  (76.1, 11.2), (76.5, 11.35),
                                  (76.85, 10.6), (76.95, 9.75),
                                  (77.0, 9.6)])
gate_items(STP3, 'STP re-lay v3 gate')
add_items(STP3)
print('STP fragments after v3 re-lay:',
      len(fragments('ULPI_STP', BOX)))
print('=== done3 ===')
