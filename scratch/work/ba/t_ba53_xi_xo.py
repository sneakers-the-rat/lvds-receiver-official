"""t_ba53: XI via XO tightening, on exp253 (model).
1. Rip STP western B excursion (76 segs).
2. Rip XO's F west run: seg centres x[71.9,76.15]
   y[9.15,10.25]. Lay tight run y9.3: (76.20,9.90)->
   (75.9,9.3)->(72.3,9.3)->(72.12,9.88). Gate + frags.
3. XI: hand leg B (75.625,18.625)->(75.6,17.0); A* B
   (75.6,17.0)->(75.75,9.95); seg (75.75,9.95)->(74.8,10.0);
   via (74.8,10.0); F legs (74.8,10.0)->(75.27,10.05)
   ->(75.75,10.3)->(76.2,10.9)->(76.25,11.35).
   Gate all; XI frags."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp253.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)


def gate(items_by_layer, label, nets):
    ps = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] in nets:
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
    return ps


rip = [it for it in pool[2]
       if it[1] == 'ULPI_STP' and it[0] == 'seg'
       and 74.3 <= C(it)[0] <= 76.0 and 13.4 <= C(it)[1] <= 17.2]
rip_items(rip)
print(f'excursion ripped {len(rip)}')

print('XO frags before:', len(fragments('XO', BOX)))
ripx = [it for it in pool[0]
        if it[1] == 'XO' and it[0] == 'seg'
        and 71.9 <= C(it)[0] <= 76.15 and 9.15 <= C(it)[1] <= 10.25]
print(f'XO run rip: {len(ripx)} segs')
rip_items(ripx)
print('XO frags mid:', len(fragments('XO', BOX)))
XONEW = {0: [('seg', 'XO', (76.20, 9.90, 75.9, 9.3, 0.10), 0.2),
             ('seg', 'XO', (75.9, 9.3, 72.3, 9.3, 0.10), 0.2),
             ('seg', 'XO', (72.3, 9.3, 72.12, 9.88, 0.10), 0.2)],
         1: [], 2: []}
gate(XONEW, 'XO new run', ('XO',))
add_items(XONEW)
print('XO frags after:', len(fragments('XO', BOX)))

astar = make_astar((70.0, 80.0, 6.0, 22.0), 0.05)
rr = astar('XI', ((2,), 75.6, 17.0), (2, 75.75, 9.95), 0.10)
print('XI A* mid->south:', 'FOUND vias=' + str(rr['vias']) if rr
      else 'NONE')
HAND = {2: [('seg', 'XI', (75.625, 18.625, 75.6, 17.0, 0.10), 0.2),
            ('seg', 'XI', (75.75, 9.95, 74.8, 10.0, 0.10), 0.2)],
        0: [], 1: []}
gate(HAND, 'XI hand B legs', ('XI',))
if rr:
    JI = journey_items_dense(rr, 'XI', hw=0.10)
    gate(JI, 'XI A* drop', ('XI',))
    for run in rr['runs']:
        pts = run['pts']
        print(f"  run {LAYN[run['layer']]} npts {len(pts)}: "
              + ' '.join(f"({p[0]:.2f},{p[1]:.2f})"
                         for i, p in enumerate(pts)
                         if i % 20 == 0 or i == len(pts) - 1))
    json.dump(rr, open('scratch/work/ba/design_xi_drop3.json', 'w'))
    add_items(JI)
    add_items(HAND)
    FIN = {0: [('seg', 'XI', (74.8, 10.0, 75.27, 10.05, 0.10), 0.2),
               ('seg', 'XI', (75.27, 10.05, 75.75, 10.3, 0.10), 0.2),
               ('seg', 'XI', (75.75, 10.3, 76.2, 10.9, 0.10), 0.2),
               ('seg', 'XI', (76.2, 10.9, 76.25, 11.35, 0.10), 0.2)],
           1: [], 2: []}
    GV = {l: [('via', 'XI', (74.8, 10.0, 0.25), 0.2)] for l in range(3)}
    gate(FIN, 'XI F legs', ('XI',))
    gate(GV, 'XI final via', ('XI',))
    add_items(FIN)
    add_items(GV)
    fr = fragments('XI', BOX)
    print('XI frags final:', len(fr))
    for f in fr:
        print('   terms:', sorted(f['terms'])[:6])
print('=== done ===')
