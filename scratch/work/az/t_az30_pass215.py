"""t_az30: pass-215 (PHY heal) full model verification.
Config: STP mega-rip + STP re-lay v2 (In2 hop) + CK jog v3
+ PHY loop x77.15 + PHY A* journey + PHY tail rip.
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
NETS = ['ULPI_STP', 'PHY_1V8', 'ULPI_CK', 'XI']
base = {n: len(fragments(n, BOX)) for n in NETS}
print('faithful fragments:', base)
fr = fragments('ULPI_STP', BOX)
for i, f in enumerate(fr):
    print(f'  STP frag{i}: {len(f["items"])} items, sample:',
          [L.fmt_it(it) for (l, it) in f['items'][:2]])

# CK jog v3
ck = [it for it in pool[1] if it[1] == 'ULPI_CK' and it[0] == 'seg'
      and abs(it[2][0] - 74.625) < 0.01 and abs(it[2][2] - 74.625) < 0.01
      and abs(it[2][1] - 13.5) < 0.01 and abs(it[2][3] - 6.375) < 0.01]
rip_items(ck)
print('CK vertical ripped:', len(ck))
NCK = {1: [seg('ULPI_CK', 74.625, 13.5, 74.45, 12.7, 0.125),
           seg('ULPI_CK', 74.45, 12.7, 74.45, 10.2, 0.125),
           seg('ULPI_CK', 74.45, 10.2, 74.625, 9.4, 0.125),
           seg('ULPI_CK', 74.625, 9.4, 74.625, 6.375, 0.125)]}
add_items(NCK)
gate_items(NCK, 'CK jog v3 gate')

# STP mega-rip + re-lay v2
mg = [it for it in pool[2] if it[1] == 'ULPI_STP' and it[0] == 'seg'
      and 75.8 < C(it)[0] < 77.05 and 9.45 < C(it)[1] < 13.45]
rip_items(mg)
print('STP mega-ripped:', len(mg))
fr = fragments('ULPI_STP', BOX)
print('STP fragments after mega-rip:', len(fr))
for i, f in enumerate(fr):
    print(f'  frag{i}: {len(f["items"])} items, sample:',
          [L.fmt_it(it) for (l, it) in f['items'][:2]])
NSTP = {0: [via('ULPI_STP', 74.92, 11.9), via('ULPI_STP', 75.95, 11.15)],
        1: [via('ULPI_STP', 74.92, 11.9), via('ULPI_STP', 75.95, 11.15),
            seg('ULPI_STP', 74.92, 11.9, 75.95, 11.15)],
        2: [via('ULPI_STP', 74.92, 11.9), via('ULPI_STP', 75.95, 11.15),
            seg('ULPI_STP', 76.10, 13.50, 75.50, 13.35),
            seg('ULPI_STP', 75.50, 13.35, 75.30, 13.10),
            seg('ULPI_STP', 75.30, 13.10, 74.92, 11.90),
            seg('ULPI_STP', 75.95, 11.15, 76.30, 11.55),
            seg('ULPI_STP', 76.30, 11.55, 76.75, 10.50),
            seg('ULPI_STP', 76.75, 10.50, 76.90, 9.70),
            seg('ULPI_STP', 76.90, 9.70, 77.00, 9.60)]}
add_items(NSTP)
gate_items(NSTP, 'STP re-lay v2 gate')
print('STP fragments after re-lay:', len(fragments('ULPI_STP', BOX)))

# PHY loop
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

# PHY journey (regenerate A* deterministically on this pool minus
# STP/CK changes? No: A* was run on STP-ripped+loop pool. Re-run
# here on the CURRENT pool for exactness.)
astar = make_astar((70.0, 88.0, 8.0, 23.0), 0.05)
r = astar('PHY_1V8', ((0,), 72.02, 18.0), (2, 77.8, 16.2), 0.10)
print('PHY A* on final pool:', 'FOUND vias=' + str(r['vias']) if r
      else 'none')
if r:
    JI = journey_items_dense(r, 'PHY_1V8', hw=0.10)
    gate_items(JI, 'PHY journey gate (final pool)')
    add_items(JI)
    json.dump(r, open('scratch/work/az/design215_phy.json', 'w'))
    print('journey saved to design215_phy.json')
# PHY tail rip
tl = [it for it in pool[0] if it[1] == 'PHY_1V8' and it[0] == 'seg'
      and C(it)[0] < 71.8 and C(it)[1] > 17.4]
rip_items(tl)
print('PHY tail ripped:', len(tl))
fin = {n: len(fragments(n, BOX)) for n in NETS}
print('final fragments:', fin, '(faithful:', base, ')')
print('=== done ===')
