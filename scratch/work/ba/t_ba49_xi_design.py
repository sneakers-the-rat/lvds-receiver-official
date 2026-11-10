"""t_ba49: XI drop design on exp253.
Step 1: rip STP's western B excursion (74 segs, centres
x[74.3,76.0] y[13.4,17.2] -- includes the (75.975,13.575)
boundary seg) in the model; verify STP frags unchanged
in structure (B splits at the loop joins only).
Step 2: dump 1V8A B items x[73.8,76.3] y[9.5,19].
Step 3: A* XI on B from (75.625,18.625) to (75.05,9.8);
gate; then F legs (75.05,9.8)->(75.9,10.2)->(76.2,10.9)
->(76.25,11.35) + via (75.05,9.8): gate all."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp253.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)

rip = []
for it in pool[2]:
    if it[1] != 'ULPI_STP' or it[0] != 'seg':
        continue
    cc = C(it)
    if 74.3 <= cc[0] <= 76.0 and 13.4 <= cc[1] <= 17.2:
        rip.append(it)
rip_items(rip)
print(f'excursion ripped: {len(rip)} segs')
fr = fragments('ULPI_STP', BOX)
print('STP frags after rip:', len(fr))

print('--- 1V8A B x[73.8,76.3] y[9.5,19] ---')
seen = set()
for it in pool[2]:
    if it[1] != 'PHY_1V8A':
        continue
    cc = C(it)
    if 73.8 <= cc[0] <= 76.3 and 9.5 <= cc[1] <= 19.0:
        d = it[2]
        if it[0] == 'seg':
            s = f'  seg ({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f})'
        elif it[0] == 'via':
            s = f'  via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}'
        else:
            s = f'  pad ({d[0]:.2f},{d[1]:.2f})'
        if s not in seen:
            seen.add(s)
            print(s)

astar = make_astar((70.0, 80.0, 6.0, 22.0), 0.05)
rr = astar('XI', ((2,), 75.625, 18.625), (2, 75.05, 9.8), 0.10)
print('XI B drop:', 'FOUND vias=' + str(rr['vias']) if rr else 'NONE')
if rr:
    JI = journey_items_dense(rr, 'XI', hw=0.10)
    ps = []
    for l in range(3):
        for it in JI.get(l, []):
            for o in pool[l]:
                if o[1] == 'XI':
                    continue
                m = item_margin(l, it, [o])
                if m < 0.15:
                    ps.append((round(m, 3), LAYN[l], o[1],
                               (round(C(it)[0], 2), round(C(it)[1], 2)),
                               (round(C(o)[0], 2), round(C(o)[1], 2))))
    ps.sort(key=lambda t: t[0])
    print(f'XI drop gate: neg {sum(1 for p in ps if p[0] < 0)}, '
          f'worst 6: {ps[:6]}')
    for run in rr['runs']:
        pts = run['pts']
        print(f"  run {LAYN[run['layer']]} npts {len(pts)}: "
              + ' '.join(f"({p[0]:.2f},{p[1]:.2f})"
                         for i, p in enumerate(pts)
                         if i % 25 == 0 or i == len(pts) - 1))
    if not any(p[0] < 0 for p in ps):
        json.dump(rr, open('scratch/work/ba/design_xi_drop.json', 'w'))
        add_items(JI)
        print('XI drop placed; XI frags', len(fragments('XI', BOX)))

FLEGS = {0: [('seg', 'XI', (75.05, 9.8, 75.9, 10.2, 0.10), 0.2),
             ('seg', 'XI', (75.9, 10.2, 76.2, 10.9, 0.10), 0.2),
             ('seg', 'XI', (76.2, 10.9, 76.25, 11.35, 0.10), 0.2)]}
GV = {l: [('via', 'XI', (75.05, 9.8, 0.25), 0.2)] for l in range(3)}
for items, label in ((FLEGS, 'XI F legs'), (GV, 'XI final via')):
    ps = []
    for l in range(3):
        for it in items.get(l, []):
            for o in pool[l]:
                if o[1] == 'XI':
                    continue
                cc, ci = C(o), C(it)
                if abs(cc[0] - ci[0]) > 3.5 or abs(cc[1] - ci[1]) > 3.5:
                    continue
                m = item_margin(l, it, [o])
                if m < 0.15:
                    ps.append((round(m, 3), LAYN[l], o[1],
                               (round(ci[0], 2), round(ci[1], 2)),
                               (round(cc[0], 2), round(cc[1], 2))))
    ps.sort(key=lambda t: t[0])
    print(f'{label}: neg {sum(1 for p in ps if p[0] < 0)}, '
          f'worst 6: {ps[:6]}')
print('=== done ===')
