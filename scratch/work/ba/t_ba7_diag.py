"""t_ba7 diagnostics:
A) fence dumps (B + In2) for x[69,77.5] y[9.5,20], excluding
   {PHY_1V8A, ULPI_STP, PHY_1V8}.
B) rebuild t_ba6 config (PHY placed, STP chain ripped, snake
   ripped, tail via+F tail KEPT this time); place STP S1 journey;
   gate S1 with coordinates (all pairs < +0.06).
C) 1V8A A* goal = old tail via point (71.48,15.38) on B.
D) if C fails: 1V8A A* goal = C23.1 F pad (repeat of t_ba6)."""
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


pool = load_board_pool(BOARD)

print('--- A) fences x[69,77.5] y[9.5,20] (excl 1V8A/STP/PHY) ---')
for l in (2, 1):
    seen = []
    for it in pool[l]:
        if it[1] in ('PHY_1V8A', 'ULPI_STP', 'PHY_1V8'):
            continue
        cc = C(it)
        if 69 <= cc[0] <= 77.5 and 9.5 <= cc[1] <= 20:
            d = it[2]
            if it[0] == 'seg':
                seen.append(f'{LAYN[l]} {it[1]} seg ({d[0]:.2f},{d[1]:.2f})'
                            f'->({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')
            elif it[0] == 'via':
                seen.append(f'{LAYN[l]} {it[1]} via ({d[0]:.2f},{d[1]:.2f})'
                            f' r{d[2]}')
            elif it[0] == 'pad':
                seen.append(f'{LAYN[l]} {it[1]} pad ({d[0]:.2f},{d[1]:.2f})')
    for s in sorted(set(seen)):
        print('  ', s)

# ---- rebuild t_ba6 config ----
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
rip_items(snake)
print(f'config rebuilt: snake ripped {len(snake)}; tail via KEPT; '
      f'1V8A frags {len(fragments("PHY_1V8A", BOX))}')

# ---- B) place S1, gate with coordinates ----
S1 = json.load(open('scratch/work/ba/design_stp_s1.json'))
JI = journey_items_dense(S1, 'ULPI_STP', hw=0.10)
pairs = []
for l in range(3):
    for it in JI.get(l, []):
        for o in pool[l]:
            if o[1] == it[1]:
                continue
            m = item_margin(l, it, [o])
            if m < 0.06:
                pairs.append((round(m, 3), LAYN[l], it[1], o[1],
                              (round(C(it)[0], 2), round(C(it)[1], 2)),
                              (round(C(o)[0], 2), round(C(o)[1], 2))))
pairs.sort(key=lambda t: t[0])
print(f'B) S1 pairs < +0.06: {len(pairs)}')
for p in pairs[:14]:
    print('   ', p)
add_items(JI)
print('STP frags after S1:', len(fragments('ULPI_STP', BOX)))

# ---- C) 1V8A A* to the kept tail via point on B ----
astar = make_astar(DBOX, 0.05)
r2 = astar('PHY_1V8A', ((2, 1, 0), 74.90, 11.75), (2, 71.48, 15.38), 0.10)
print('C) 1V8A -> tail via (B):',
      'FOUND vias=' + str(r2['vias']) if r2 else 'NONE')
if r2:
    JI2 = journey_items_dense(r2, 'PHY_1V8A', hw=0.10)
    neg = 0
    worst = []
    for l in range(3):
        for it in JI2.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                m = item_margin(l, it, [o])
                if m < 0.3:
                    worst.append((round(m, 3), LAYN[l], o[1]))
                    if m < 0:
                        neg += 1
    worst.sort(key=lambda t: t[0])
    print(f'C) gate: neg {neg}, worst 4: {worst[:4]}')
    add_items(JI2)
    json.dump(r2, open('scratch/work/ba/design_1v8a_c.json', 'w'))
else:
    r3 = astar('PHY_1V8A', ((2, 1, 0), 74.90, 11.75), (0, 71.525, 14.750),
               0.10)
    print('D) 1V8A -> C23.1 F pad:',
          'FOUND vias=' + str(r3['vias']) if r3 else 'NONE')
print('final frags: PHY', len(fragments('PHY_1V8', BOX)),
      'STP', len(fragments('ULPI_STP', BOX)),
      '1V8A', len(fragments('PHY_1V8A', BOX)),
      'CK', len(fragments('ULPI_CK', BOX)),
      'XI', len(fragments('XI', BOX)),
      'XO', len(fragments('XO', BOX)))
print('=== done ===')
