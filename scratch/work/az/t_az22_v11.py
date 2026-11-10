"""t_az22: v11 — STP mega-rip (one box), single re-lay chain,
PHY loop x77.15, XI hand journey (fixed hop), A* PHY full print.
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


def via(net, x, y, r=0.25, clr=0.2):
    return ('via', net, (x, y, r), clr)


def path_items(net, layer, pts, hw=0.10, clr=0.2):
    out = []
    for i in range(len(pts) - 1):
        out.append(seg(net, pts[i][0], pts[i][1], pts[i + 1][0],
                       pts[i + 1][1], hw, clr))
    return {layer: out}


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


pool = load_board_pool(BOARD)
NETS = ['ULPI_STP', 'PHY_1V8A', 'XO', 'PHY_1V8', 'XI']
base = {n: len(fragments(n, BOX)) for n in NETS}
print('faithful fragments:', base)

# notch
rip_items([it for l in range(3) for it in pool[l]
           if it[1] == 'PHY_1V8A' and it[0] == 'via'
           and abs(it[2][0] - 75.737) < 0.01
           and abs(it[2][1] - 10.75) < 0.01])
rip_items([it for it in pool[0] if it[1] == 'PHY_1V8A'
           and it[0] == 'seg' and abs(it[2][0] - 75.72) < 0.01
           and abs(it[2][1] - 11.0) < 0.01 and it[2][3] < 11.0])
rip_items([it for it in pool[2] if it[1] == 'PHY_1V8A'
           and it[0] == 'seg' and abs(it[2][0] - 75.737) < 0.01
           and abs(it[2][1] - 10.75) < 0.01])
N1 = {0: [via('PHY_1V8A', 75.30, 10.30, 0.25, 0.25),
          seg('PHY_1V8A', 75.72, 11.0, 75.45, 10.50, 0.10, 0.25),
          seg('PHY_1V8A', 75.45, 10.50, 75.30, 10.30, 0.10, 0.25)],
      1: [via('PHY_1V8A', 75.30, 10.30, 0.25, 0.25)],
      2: [via('PHY_1V8A', 75.30, 10.30, 0.25, 0.25),
          seg('PHY_1V8A', 75.30, 10.30, 75.30, 11.35, 0.10, 0.25)]}
add_items(N1)

# XO jog
try:
    ch = chain_segs(pool, 'XO', 0, (76.75, 11.125), (75.9, 9.7))
    rip_items(ch)
    print('XO chain ripped:', len(ch))
except SystemExit as e:
    print('XO chain FAILED', e)
N2 = {0: [seg('XO', 76.75, 11.125, 76.62, 10.80),
          seg('XO', 76.62, 10.80, 76.60, 10.05),
          seg('XO', 76.60, 10.05, 76.05, 9.80),
          seg('XO', 76.05, 9.80, 75.90, 9.70)], 1: [], 2: []}
add_items(N2)

# STP mega-rip: B segs centre in x[75.8,77.05] y[9.45,13.45]
mg = [it for it in pool[2] if it[1] == 'ULPI_STP' and it[0] == 'seg'
      and 75.8 < C(it)[0] < 77.05 and 9.45 < C(it)[1] < 13.45]
rip_items(mg)
print('STP mega-ripped:', len(mg))
N3 = {0: [], 1: [], 2: [
    seg('ULPI_STP', 76.10, 13.50, 75.45, 13.25),
    seg('ULPI_STP', 75.45, 13.25, 75.45, 12.10),
    seg('ULPI_STP', 75.45, 12.10, 75.75, 11.88),
    seg('ULPI_STP', 75.75, 11.88, 76.00, 11.85),
    seg('ULPI_STP', 76.00, 11.85, 76.30, 11.55),
    seg('ULPI_STP', 76.30, 11.55, 76.75, 10.50),
    seg('ULPI_STP', 76.75, 10.50, 76.90, 9.70),
    seg('ULPI_STP', 76.90, 9.70, 77.00, 9.60)]}
add_items(N3)

# PHY loop x77.15
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

now = {n: len(fragments(n, BOX)) for n in NETS}
print('v11 fragments after re-lays:', now, '(faithful:', base, ')')
for lbl, NN in [('notch', N1), ('XO jog', N2), ('STP relay', N3),
                ('PHY loop', N4)]:
    gate_items(NN, f'{lbl} gate')

# A* PHY, full journey print
astar = make_astar((70.0, 88.0, 8.0, 23.0), 0.05)
r = astar('PHY_1V8', ((0,), 72.02, 18.0), (2, 77.8, 16.2), 0.10)
print('PHY A* C22.1 -> B joint:', 'FOUND' if r else 'none')
if r:
    print('  vias:', r['vias'])
    for rn in r['runs']:
        print(f"  L{rn['layer']} pts: {rn['pts']}")
    gate_items(journey_items_dense(r, 'PHY_1V8', hw=0.10),
               'PHY A* journey gate')

# XI hand journey (fixed hop)
XI_F = path_items('XI', 0, [(76.25, 11.562), (76.25, 11.05),
                            (76.06, 10.42)])
XI_V = {0: [via('XI', 76.06, 10.42)], 1: [via('XI', 76.06, 10.42)],
        2: [via('XI', 76.06, 10.42)]}
XI_B = path_items('XI', 2, [(76.06, 10.42), (76.30, 11.20),
                            (76.32, 12.20), (76.60, 13.35),
                            (76.60, 16.90), (77.30, 17.50),
                            (76.90, 18.30), (75.625, 18.625)])
gate_items(XI_F, 'XI F hop gate (pre-add)')
gate_items(XI_V, 'XI dive gate (pre-add)')
gate_items(XI_B, 'XI B ride gate (pre-add)')
add_items(XI_F); add_items(XI_V); add_items(XI_B)
fin = {n: len(fragments(n, BOX)) for n in NETS}
print('v11 fragments final:', fin, '(faithful:', base, ')')
print('=== done ===')
