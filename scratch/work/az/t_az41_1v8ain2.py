"""t_az41: pass-215 assembly attempt 4.
Base: STP chain rip + PHY loop + notch re-lay v2 + PHY A* journey
(astar4) + tail rip [proven pieces].
Then:
 (6) PHY_1V8A journey B->In2: rip B head (75.3,10.3)... wait notch
     re-lay v2's B head (75.30,10.30)->(75.05,10.95)->(74.90,11.75)
     AND the B journey chain (74.9,11.75)->(71.48,15.38).
     Add In2 run from notch via (75.30,10.30):
     (75.35,10.15)->(74.85,9.05)->(73.80,9.00)->(72.40,10.50)
     ->(71.90,12.50)->(71.48,15.38). Gate; 1V8A frags 1.
 (7) STP descent v5 (B): (74.55,14.75)->(73.90,15.30)
     ->(73.30,15.20)->(73.30,14.20)->(73.70,13.40)->(74.30,12.60)
     ->(74.90,11.90)->(75.60,11.00)->(76.30,10.50)->(76.95,9.85)
     ->(77.00,9.60). Gate; STP frags 1.
"""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'
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
                    worst.append((round(m, 3), l, it, o))
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


def path_items(net, layer, pts, hw=0.10, clr=0.25):
    out = []
    for i in range(len(pts) - 1):
        out.append(seg(net, pts[i][0], pts[i][1], pts[i + 1][0],
                       pts[i + 1][1], hw, clr))
    return {layer: out}


pool = load_board_pool(BOARD)
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
nv = [it for it in pool[0] if it[1] == 'PHY_1V8A' and it[0] == 'via'
      and abs(it[2][0] - 75.7375) < 0.01 and abs(it[2][1] - 10.75) < 0.01]
rip_items(nv)
rip_pair('PHY_1V8A', 0, (75.72, 11.0), (75.7375, 10.75))
rip_pair('PHY_1V8A', 2, (75.7375, 10.75), (75.30, 11.35))
NN = {0: [seg('PHY_1V8A', 75.72, 11.0, 75.48, 10.68, 0.10, 0.25),
          seg('PHY_1V8A', 75.48, 10.68, 75.30, 10.30, 0.10, 0.25),
          via('PHY_1V8A', 75.30, 10.30, 0.25, 0.25)],
      1: [via('PHY_1V8A', 75.30, 10.30, 0.25, 0.25)],
      2: [via('PHY_1V8A', 75.30, 10.30, 0.25, 0.25),
          seg('PHY_1V8A', 75.30, 10.30, 75.05, 10.95, 0.10, 0.25),
          seg('PHY_1V8A', 75.05, 10.95, 74.90, 11.75, 0.10, 0.25)]}
add_items(NN)
rp = json.load(open('scratch/work/az/design_phy_astar4.json'))
add_items(journey_items_dense(rp, 'PHY_1V8', hw=0.10))
tl = [it for it in pool[0] if it[1] == 'PHY_1V8' and it[0] == 'seg'
      and C(it)[0] < 71.8 and C(it)[1] > 17.4]
rip_items(tl)
print('base pool: PHY', len(fragments('PHY_1V8', BOX)),
      'STP', len(fragments('ULPI_STP', BOX)),
      '1V8A', len(fragments('PHY_1V8A', BOX)))

# (6) 1V8A B journey out, In2 run in
m = 0
m += rip_pair('PHY_1V8A', 2, (75.30, 10.30), (75.05, 10.95))
m += rip_pair('PHY_1V8A', 2, (75.05, 10.95), (74.90, 11.75))
print('1V8A B head ripped:', m)
try:
    ch2 = chain_segs(pool, 'PHY_1V8A', 2, (74.90, 11.75), (71.48, 15.38))
    rip_items(ch2)
    print('1V8A B journey ripped:', len(ch2))
except SystemExit as e:
    print('1V8A journey chain FAILED', e)
J8 = path_items('PHY_1V8A', 1, [(75.30, 10.30), (75.35, 10.15),
                                (74.85, 9.05), (73.80, 9.00),
                                (72.40, 10.50), (71.90, 12.50),
                                (71.48, 15.38)])
add_items(J8)
gate_items(J8, '1V8A In2 run gate')
print('1V8A frags:', len(fragments('PHY_1V8A', BOX)))

# (7) STP descent v5
DESC = path_items('ULPI_STP', 2, [(74.55, 14.75), (73.90, 15.30),
                                  (73.30, 15.20), (73.30, 14.20),
                                  (73.70, 13.40), (74.30, 12.60),
                                  (74.90, 11.90), (75.60, 11.00),
                                  (76.30, 10.50), (76.95, 9.85),
                                  (77.00, 9.60)], hw=0.10, clr=0.2)
add_items(DESC)
gate_items(DESC, 'STP descent v5 gate')
print('final: STP', len(fragments('ULPI_STP', BOX)),
      'PHY', len(fragments('PHY_1V8', BOX)),
      'CK', len(fragments('ULPI_CK', BOX)),
      'XI', len(fragments('XI', BOX)),
      '1V8A', len(fragments('PHY_1V8A', BOX)),
      'XO', len(fragments('XO', BOX)))
print('=== done ===')
