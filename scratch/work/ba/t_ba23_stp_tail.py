"""t_ba23: STP re-plan v2. Dump STP items with centre y<8.5
(the southern wander), then: keep F stub + dive via + B legs
and the final approach (items with centre y<-0.5 plus the
chain into U6.26), rip the southern chain (y in [7.5,13.6]
east items + mid wander), A* (76.10,13.50) B -> via point
(70.25,-2.20) layers-free. Gate + occupancy report."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)

print('--- STP items centre y<8.5 ---')
for l in range(3):
    for it in pool[l]:
        if it[1] != 'ULPI_STP':
            continue
        cc = C(it)
        if cc[1] < 8.5:
            d = it[2]
            if it[0] == 'seg':
                print(f'  {LAYN[l]} seg ({d[0]:.2f},{d[1]:.2f})->'
                      f'({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')
            elif it[0] == 'via':
                print(f'  {LAYN[l]} via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}')

# rip: STP segs/vias whose centre is in the southern chain
# district x[75.5,78] y[7,14] (chain + dive vias) plus mid
# wander items with centre y in (0.5, 7.5) and x > 72
rip = []
for l in range(3):
    for it in pool[l]:
        if it[1] != 'ULPI_STP' or it[0] not in ('seg', 'via'):
            continue
        cc = C(it)
        if 75.5 <= cc[0] <= 78.5 and 7.0 <= cc[1] <= 14.0:
            rip.append(it)
        elif 0.5 < cc[1] < 7.5 and cc[0] > 72.0:
            rip.append(it)
rip_items(rip)
print(f'ripped {len(rip)} southern/mid STP items; frags '
      f'{len(fragments("ULPI_STP", BOX))}')

astar = make_astar((64.0, 84.0, -6.0, 22.0), 0.05)
rr = astar('ULPI_STP', ((2,), 76.10, 13.50), (2, 70.25, -2.20), 0.10)
print('re-plan legs-end -> (70.25,-2.20) B:',
      'FOUND vias=' + str(rr['vias']) if rr else 'NONE')
if not rr:
    rr = astar('ULPI_STP', ((2, 1, 0), 76.10, 13.50), (2, 70.25, -2.20),
               0.10)
    print('re-plan (start layers free):',
          'FOUND vias=' + str(rr['vias']) if rr else 'NONE')
if rr:
    JI = journey_items_dense(rr, 'ULPI_STP', hw=0.10)
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
    print(f'gate: neg {neg}, worst 6: {pairs[:6]}')
    for run in rr['runs']:
        pts = run['pts']
        print(f"  run {LAYN[run['layer']]} npts {len(pts)}: "
              + ' '.join(f"({p[0]:.1f},{p[1]:.1f})"
                         for i, p in enumerate(pts)
                         if i % 20 == 0 or i == len(pts) - 1))
    print('  vias:', rr['vias'])
    if neg == 0:
        json.dump(rr, open('scratch/work/ba/design_stp_south.json', 'w'))
        add_items(JI)
        print('SAVED; STP frags', len(fragments('ULPI_STP', BOX)))
print('=== done ===')
