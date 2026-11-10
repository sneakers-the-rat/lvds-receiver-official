"""t_ba15 facts + hand gate:
1) +5V In2 items (all) with endpoints.
2) F items in x[70,76.5] y[8.5,13.8].
3) Hand-gate the 1V8A design: F south channel y10.82 from
   U7.29 west to x72.15, F stub north to via (72.15,11.30),
   In2 ascent (71.8,12.3)->(71.75,13.3)->(71.6,14.6)->tail via
   (71.48,15.38). Config: tuned STP + ba PHY placed, 1V8A
   routed copper ripped."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}

pool = load_board_pool(BOARD)
print('--- +5V In2 items ---')
for it in pool[1]:
    if it[1] == '+5V':
        d = it[2]
        if it[0] == 'seg':
            print(f'   seg ({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f})'
                  f' hw{d[4]}')
        else:
            print(f'   {it[0]} ({d[0]:.2f},{d[1]:.2f}) r{d[2]}')
print('--- F items x[70,76.5] y[8.5,13.8] ---')
for it in pool[0]:
    cc = C(it)
    if 70 <= cc[0] <= 76.5 and 8.5 <= cc[1] <= 13.8:
        d = it[2]
        if it[0] == 'seg':
            print(f'   {it[1]} seg ({d[0]:.2f},{d[1]:.2f})->'
                  f'({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')
        elif it[0] == 'via':
            print(f'   {it[1]} via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}')
        else:
            print(f'   {it[1]} pad ({d[0]:.2f},{d[1]:.2f})')


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


# config: rip 1V8A copper + STP chain; place ba PHY + tuned STP
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
r = json.load(open('scratch/work/ba/design_phy_ba.json'))
add_items(journey_items_dense(r, 'PHY_1V8', hw=0.10))
tl = [it for it in pool[0] if it[1] == 'PHY_1V8' and it[0] == 'seg'
      and C(it)[0] < 71.8 and C(it)[1] > 17.4]
rip_items(tl)
ST = json.load(open('scratch/work/ba/design_stp_tuned.json'))
add_items(journey_items_dense(ST, 'ULPI_STP', hw=0.10))
print('config placed')

F_RUN = [(75.75, 11.5625), (75.75, 10.82), (72.15, 10.82), (72.15, 11.30)]
IN2_RUN = [(72.15, 11.30), (71.80, 12.30), (71.75, 13.30),
           (71.60, 14.60), (71.48, 15.38)]
items = {0: [], 1: [], 2: []}
for a, b in zip(F_RUN, F_RUN[1:]):
    items[0].append(seg('PHY_1V8A', a[0], a[1], b[0], b[1], 0.10, 0.25))
for a, b in zip(IN2_RUN, IN2_RUN[1:]):
    items[1].append(seg('PHY_1V8A', a[0], a[1], b[0], b[1], 0.10, 0.25))
items[0].append(('via', 'PHY_1V8A', (72.15, 11.30, 0.25), 0.25))
items[1].append(('via', 'PHY_1V8A', (72.15, 11.30, 0.25), 0.25))
items[2].append(('via', 'PHY_1V8A', (72.15, 11.30, 0.25), 0.25))
pairs = []
for l in range(3):
    for it in items[l]:
        for o in pool[l]:
            if o[1] == 'PHY_1V8A':
                continue
            m = item_margin(l, it, [o])
            if m < 0.15:
                pairs.append((round(m, 3), LAYN[l], o[1],
                              (round(C(it)[0], 2), round(C(it)[1], 2)),
                              (round(C(o)[0], 2), round(C(o)[1], 2))))
pairs.sort(key=lambda t: t[0])
print(f'hand design gate: pairs<0.15 {len(pairs)}, '
      f'neg {sum(1 for p in pairs if p[0] < 0)}')
for p in pairs[:14]:
    print('   ', p)
print('=== done ===')
