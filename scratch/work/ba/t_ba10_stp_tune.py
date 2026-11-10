"""t_ba10: hand-tune STP S1's pinch around PHY's journey west end.
Rebuild t_ba9 config (PHY placed, 1V8A copper ripped, STP chain
ripped). STP polyline = S1 pts up to the inbound anchor near
(73.5,16.9), a hand spiral around PHY's via (71.9,17.8) at
r=0.615 (tangent between PHY-via R0.60 disc and XO-via R0.55
disc), then S1 pts from the exit anchor near (72.2,16.6).
Exact-gate the tuned journey; print worst pairs with centres."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
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


pool = load_board_pool(BOARD)
v1 = [it for l in range(3) for it in pool[l]
      if it[1] == 'PHY_1V8A' and it[0] in ('seg', 'via')]
rip_items(v1)
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
# ba iteration 5: shift PHY journey B pts x in [72.1,72.6] south
# by 0.05 -- opens the inbound-leg channel vs STP without moving
# STP's leg into the GND via (73.43,17.68).
for run in r['runs']:
    if run['layer'] == 2:
        run['pts'] = [[p[0], p[1] - 0.05] if 72.1 <= p[0] <= 72.6
                      else p for p in run['pts']]
JI_PHY = journey_items_dense(r, 'PHY_1V8', hw=0.10)
ppairs = []
for l in range(3):
    for it in JI_PHY.get(l, []):
        for o in pool[l]:
            if o[1] == it[1]:
                continue
            m = item_margin(l, it, [o])
            if m < 0.1:
                ppairs.append((round(m, 3), LAYN[l], o[1]))
ppairs.sort(key=lambda t: t[0])
print(f'PHY journey (shifted) gate: neg '
      f'{sum(1 for p in ppairs if p[0] < 0)}, worst 5: {ppairs[:5]}')
add_items(JI_PHY)
json.dump(r, open('scratch/work/ba/design_phy_ba.json', 'w'))
tl = [it for it in pool[0] if it[1] == 'PHY_1V8' and it[0] == 'seg'
      and C(it)[0] < 71.8 and C(it)[1] > 17.4]
rip_items(tl)
print('config rebuilt; PHY frags', len(fragments('PHY_1V8', BOX)))

S1 = json.load(open('scratch/work/ba/design_stp_freed_s1.json'))
pts = [tuple(p) for p in S1['runs'][0]['pts']]


def nearest_idx(pts, x, y):
    return min(range(len(pts)),
               key=lambda i: (pts[i][0] - x) ** 2 + (pts[i][1] - y) ** 2)


i_in = nearest_idx(pts, 72.45, 18.05)
i_out = nearest_idx(pts, 72.2, 16.6)
print(f'inbound anchor idx {i_in} = {pts[i_in]}; exit anchor idx '
      f'{i_out} = {pts[i_out]}')
head = pts[:i_in + 1]
tail = pts[i_out:]
# spiral around PHY via (71.9,17.8) at r=0.63, 20-degree steps
# (chord sag 0.0096 -> min radius 0.620 -> +0.020 vs the R0.60
# forbidden disc; XO via disc R0.55 clears by >= +0.05)
SPIRAL = [(72.416, 18.161), (72.261, 18.316), (72.063, 18.408),
          (71.845, 18.428), (71.634, 18.371), (71.455, 18.245),
          (71.329, 18.066), (71.272, 17.855), (71.291, 17.637),
          (71.384, 17.439), (71.539, 17.283)]
newpts = head + SPIRAL + tail
# dedupe consecutive duplicates
clean = [newpts[0]]
for p in newpts[1:]:
    if abs(p[0] - clean[-1][0]) > 1e-9 or abs(p[1] - clean[-1][1]) > 1e-9:
        clean.append(p)
design = {'vias': [], 'runs': [{'layer': 2, 'pts': [list(p) for p in clean]}]}
JI = journey_items_dense(design, 'ULPI_STP', hw=0.10)
pairs = []
for l in range(3):
    for it in JI.get(l, []):
        for o in pool[l]:
            if o[1] == it[1]:
                continue
            m = item_margin(l, it, [o])
            if m < 0.1:
                pairs.append((round(m, 3), LAYN[l], o[1],
                              (round(C(it)[0], 2), round(C(it)[1], 2)),
                              (round(C(o)[0], 2), round(C(o)[1], 2))))
pairs.sort(key=lambda t: t[0])
neg = sum(1 for p in pairs if p[0] < 0)
print(f'tuned STP gate: pairs<0.1 {len(pairs)}, neg {neg}')
for p in pairs[:12]:
    print('   ', p)
if neg == 0:
    json.dump(design, open('scratch/work/ba/design_stp_tuned.json', 'w'))
    add_items(JI)
    print('SAVED design_stp_tuned.json; STP frags',
          len(fragments('ULPI_STP', BOX)))
print('=== done ===')
