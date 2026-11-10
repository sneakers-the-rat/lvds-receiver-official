"""t_az31: pass-215 v2 — STP vertical detour pre-applied, PHY
loop split at (77.15,13.0), A* PHY to the split point.
Detour: rip STP B vertical segs centre x[75.9,76.1] y[12.2,13.0];
add (76.0,13.0)->(75.62,12.9)->(75.62,12.3)->(76.0,12.2).
Loop: rip 4 segs; add (77.9,10.08)->(77.5,10.25)->(77.28,10.8)
 ->(77.15,11.3)->(77.15,13.0)->(77.15,15.1)->(77.8,16.2).
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
print('faithful STP frags:', len(fragments('ULPI_STP', BOX)),
      'PHY frags:', len(fragments('PHY_1V8', BOX)))

vd = [it for it in pool[2] if it[1] == 'ULPI_STP' and it[0] == 'seg'
      and 75.9 < C(it)[0] < 76.1 and 12.2 < C(it)[1] < 13.0]
rip_items(vd)
print('STP vertical segs ripped:', len(vd))
ND = {0: [], 1: [], 2: [seg('ULPI_STP', 76.0, 13.0, 75.62, 12.9),
                       seg('ULPI_STP', 75.62, 12.9, 75.62, 12.3),
                       seg('ULPI_STP', 75.62, 12.3, 76.0, 12.2)]}
add_items(ND)
gate_items(ND, 'STP detour gate')
print('STP frags after detour:', len(fragments('ULPI_STP', BOX)))

n = 0
n += rip_pair('PHY_1V8', 2, (77.90, 10.08), (77.45, 10.10))
n += rip_pair('PHY_1V8', 2, (77.45, 10.10), (76.95, 11.05))
n += rip_pair('PHY_1V8', 2, (76.95, 11.05), (76.95, 14.988))
n += rip_pair('PHY_1V8', 2, (76.95, 14.988), (77.80, 16.20))
print('PHY loop pair-ripped:', n)
N4 = {0: [], 1: [], 2: [seg('PHY_1V8', 77.90, 10.08, 77.50, 10.25, 0.15, 0.25),
                       seg('PHY_1V8', 77.50, 10.25, 77.28, 10.80, 0.10, 0.25),
                       seg('PHY_1V8', 77.28, 10.80, 77.15, 11.30, 0.10, 0.25),
                       seg('PHY_1V8', 77.15, 11.30, 77.15, 13.00, 0.15, 0.25),
                       seg('PHY_1V8', 77.15, 13.00, 77.15, 15.10, 0.15, 0.25),
                       seg('PHY_1V8', 77.15, 15.10, 77.80, 16.20, 0.15, 0.25)]}
add_items(N4)
gate_items(N4, 'PHY loop gate')

astar = make_astar((70.0, 88.0, 8.0, 23.0), 0.05)
r = astar('PHY_1V8', ((0,), 72.02, 18.0), (2, 77.15, 13.0), 0.10)
print('PHY A* to loop split:', 'FOUND vias=' + str(r['vias']) if r
      else 'none')
if r:
    for rn in r['runs']:
        print(f"  L{rn['layer']} {len(rn['pts'])} pts "
              f"{rn['pts'][0]} -> {rn['pts'][-1]}")
    JI = journey_items_dense(r, 'PHY_1V8', hw=0.10)
    gate_items(JI, 'PHY journey gate')
    add_items(JI)
    json.dump(r, open('scratch/work/az/design215_phy.json', 'w'))
    print('journey saved')
tl = [it for it in pool[0] if it[1] == 'PHY_1V8' and it[0] == 'seg'
      and C(it)[0] < 71.8 and C(it)[1] > 17.4]
rip_items(tl)
print('PHY tail ripped:', len(tl))
print('final frags: STP', len(fragments('ULPI_STP', BOX)),
      'PHY', len(fragments('PHY_1V8', BOX)),
      'CK', len(fragments('ULPI_CK', BOX)),
      'XI', len(fragments('XI', BOX)))
print('=== done ===')

# --- appended: PHY hand journey v2 ---
def path_items(net, layer, pts, hw=0.10, clr=0.25):
    out = []
    for i in range(len(pts) - 1):
        out.append(seg(net, pts[i][0], pts[i][1], pts[i + 1][0],
                       pts[i + 1][1], hw, clr))
    return {layer: out}

PHYF = path_items('PHY_1V8', 0, [(72.02, 18.0), (71.9, 17.8)])
PHYV = {l: [('via', 'PHY_1V8', (71.9, 17.8, 0.25), 0.25)] for l in range(3)}
PHYB = path_items('PHY_1V8', 2, [(71.9, 17.8), (72.5, 17.2),
                                 (73.65, 15.9), (73.65, 14.6),
                                 (74.7, 13.0), (75.2, 12.4),
                                 (75.45, 11.9), (75.8, 11.45),
                                 (76.5, 10.3), (76.85, 10.15),
                                 (77.05, 11.3), (77.15, 13.0)])
gate_items(PHYF, 'PHY F stub gate')
gate_items(PHYV, 'PHY dive gate')
gate_items(PHYB, 'PHY B hand journey gate')
add_items(PHYF); add_items(PHYV); add_items(PHYB)
print('final frags v2: STP', len(fragments('ULPI_STP', BOX)),
      'PHY', len(fragments('PHY_1V8', BOX)),
      'CK', len(fragments('ULPI_CK', BOX)),
      'XI', len(fragments('XI', BOX)))
print('=== done2 ===')
