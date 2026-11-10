"""t_ba6: exp252 + PHY design placed + STP chain ripped + PHY_1V8A's
B snake RIPPED (everything west of the notch head, plus its F tail
via/segs) -> STP A* variants; then 1V8A A* re-plan from the notch
head (74.90,11.75) to C23.1 pad (71.525,14.750) F, with whatever STP
route was found placed. Question: do STP and a STRAIGHT 1V8A re-lay
coexist with NO part move?"""
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

# ---- PHY design placed (as t_ba1) ----
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
add_items(journey_items_dense(r, 'PHY_1V8', hw=0.10))
tl = [it for it in pool[0] if it[1] == 'PHY_1V8' and it[0] == 'seg'
      and C(it)[0] < 71.8 and C(it)[1] > 17.4]
rip_items(tl)
print('PHY placed; frags PHY', len(fragments('PHY_1V8', BOX)))

# ---- rip the 1V8A snake: B segs west of head + F tail + tail via ----
HEAD = {((75.05, 10.95), (74.90, 11.75)), ((74.90, 11.75), (75.05, 10.95)),
        ((75.27, 10.33), (75.05, 10.95)), ((75.05, 10.95), (75.27, 10.33))}
snake = []
for it in list(pool[2]):
    if it[1] != 'PHY_1V8A' or it[0] != 'seg':
        continue
    d = it[2]
    key = ((round(d[0], 2), round(d[1], 2)), (round(d[2], 2), round(d[3], 2)))
    if key in HEAD:
        continue
    cc = C(it)
    if 69.0 < cc[0] < 75.2 and 10.8 < cc[1] < 15.7:
        snake.append(it)
print('snake B segs ripped:', len(snake))
rip_items(snake)
tail = []
for it in list(pool[0]):
    if it[1] == 'PHY_1V8A' and it[0] == 'seg':
        cc = C(it)
        if 71.3 < cc[0] < 71.7 and 14.6 < cc[1] < 15.5:
            tail.append(it)
via_t = [it for it in pool[0] if it[1] == 'PHY_1V8A' and it[0] == 'via'
         and abs(it[2][0] - 71.48) < 0.01 and abs(it[2][1] - 15.38) < 0.01]
print('F tail segs ripped:', len(tail), 'tail via:', len(via_t))
rip_items(tail)
rip_items(via_t)
print('1V8A frags after snake rip:', len(fragments('PHY_1V8A', BOX)))

astar = make_astar(DBOX, 0.05)


def try_stp(name, start, goal, save):
    r = astar('ULPI_STP', start, goal, 0.10)
    print(f'{name}:', 'FOUND vias=' + str(r['vias']) if r else 'NONE')
    if r:
        JI = journey_items_dense(r, 'ULPI_STP', hw=0.10)
        gate_exact(JI, f'{name} exact gate')
        add_items(JI)
        json.dump(r, open(save, 'w'))
        print(f'{name}: STP frags', len(fragments('ULPI_STP', BOX)))
        return True
    return False


ok = try_stp('S1 legs-end->(77.0,9.6)', ((2, 1, 0), 76.10, 13.50),
             (2, 77.0, 9.6), 'scratch/work/ba/design_stp_s1.json')
if not ok:
    legs = [it for it in list(pool[2])
            if it[1] == 'ULPI_STP' and it[0] == 'seg'
            and 75.8 < C(it)[0] < 76.4 and 13.4 < C(it)[1] < 18.0]
    rip_items(legs)
    print('S2: B legs ripped:', len(legs))
    ok = try_stp('S2 dive->(77.0,9.6)', ((2, 1, 0), 76.065, 17.96),
                 (2, 77.0, 9.6), 'scratch/work/ba/design_stp_s2.json')
if not ok:
    stub = [it for it in list(pool[0])
            if it[1] == 'ULPI_STP' and it[0] == 'seg'
            and 75.9 < C(it)[0] < 76.5 and 16.2 < C(it)[1] < 18.2]
    dive = [it for it in pool[0] if it[1] == 'ULPI_STP' and it[0] == 'via'
            and abs(it[2][0] - 76.065) < 0.01
            and abs(it[2][1] - 17.96) < 0.01]
    rip_items(stub)
    rip_items(dive)
    print('S3: F stub ripped:', len(stub), 'dive via:', len(dive))
    ok = try_stp('S3 U7.13pad->(77.0,9.6)', ((0, 1, 2), 76.25, 16.4375),
                 (2, 77.0, 9.6), 'scratch/work/ba/design_stp_s3.json')

# ---- 1V8A re-plan: notch head -> C23.1 pad ----
r2 = astar('PHY_1V8A', ((2, 1, 0), 74.90, 11.75), (0, 71.525, 14.750), 0.10)
print('1V8A re-plan:', 'FOUND vias=' + str(r2['vias']) if r2 else 'NONE')
if r2:
    JI2 = journey_items_dense(r2, 'PHY_1V8A', hw=0.10)
    gate_exact(JI2, '1V8A re-plan exact gate')
    add_items(JI2)
    json.dump(r2, open('scratch/work/ba/design_1v8a_replan.json', 'w'))
print('final frags: PHY', len(fragments('PHY_1V8', BOX)),
      'STP', len(fragments('ULPI_STP', BOX)),
      '1V8A', len(fragments('PHY_1V8A', BOX)),
      'CK', len(fragments('ULPI_CK', BOX)),
      'XI', len(fragments('XI', BOX)),
      'XO', len(fragments('XO', BOX)))
print('=== done ===')
