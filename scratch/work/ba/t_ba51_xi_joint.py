"""t_ba51: XI joint design v2 on exp253.
Model ops: rip STP excursion (76 B segs); rip 1V8A notch
journey (F stub 2 segs + via + B head 4 segs); place re-laid
1V8A: via (75.45,10.85), F stub (75.72,11.0)->(75.55,10.95)
->via, B head via->(74.9,11.35)->(74.3,11.95)->(73.50,12.55).
Gate 1V8A (frags + margins). Then A* XI B (step 0.125)
(75.625,18.625)->(75.375,10.5); gate; F legs + via gate."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp253.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)


def gate(items_by_layer, label, skip=('PHY_1V8A', 'XI')):
    ps = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] in skip:
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


# --- rip STP excursion ---
rip = [it for it in pool[2]
       if it[1] == 'ULPI_STP' and it[0] == 'seg'
       and 74.3 <= C(it)[0] <= 76.0 and 13.4 <= C(it)[1] <= 17.2]
rip_items(rip)
print(f'excursion ripped {len(rip)}')

# --- rip 1V8A notch journey ---
def find_seg(pool_l, net, a, b):
    out = []
    for it in pool_l:
        if it[1] != net or it[0] != 'seg':
            continue
        d = it[2]
        if (abs(d[0] - a[0]) < 0.02 and abs(d[1] - a[1]) < 0.02
                and abs(d[2] - b[0]) < 0.02 and abs(d[3] - b[1]) < 0.02) or \
           (abs(d[0] - b[0]) < 0.02 and abs(d[1] - b[1]) < 0.02
                and abs(d[2] - a[0]) < 0.02 and abs(d[3] - a[1]) < 0.02):
            out.append(it)
    return out

rip2 = []
rip2 += find_seg(pool[0], 'PHY_1V8A', (75.72, 11.0), (75.49, 10.69))
rip2 += find_seg(pool[0], 'PHY_1V8A', (75.49, 10.69), (75.27, 10.33))
rip2 += find_seg(pool[2], 'PHY_1V8A', (75.27, 10.33), (75.05, 10.95))
rip2 += find_seg(pool[2], 'PHY_1V8A', (75.05, 10.95), (74.90, 11.75))
rip2 += find_seg(pool[2], 'PHY_1V8A', (74.90, 11.75), (74.20, 12.25))
rip2 += find_seg(pool[2], 'PHY_1V8A', (74.20, 12.25), (73.50, 12.55))
for l in range(3):
    for it in pool[l]:
        if it[1] == 'PHY_1V8A' and it[0] == 'via' \
                and abs(it[2][0] - 75.27) < 0.02 \
                and abs(it[2][1] - 10.33) < 0.02:
            rip2.append(it)
print('notch journey rip found:', len(rip2), '(expect 9: 2F+4B segs'
      ' + via x3 layers)')
rip_items(rip2)
print('1V8A frags mid:', len(fragments('PHY_1V8A', BOX)))

NEW1V8A = {
    0: [('seg', 'PHY_1V8A', (75.72, 11.0, 75.55, 10.95, 0.10), 0.2),
        ('seg', 'PHY_1V8A', (75.55, 10.95, 75.45, 10.85, 0.10), 0.2),
        ('via', 'PHY_1V8A', (75.45, 10.85, 0.25), 0.2)],
    1: [('via', 'PHY_1V8A', (75.45, 10.85, 0.25), 0.2)],
    2: [('via', 'PHY_1V8A', (75.45, 10.85, 0.25), 0.2),
        ('seg', 'PHY_1V8A', (75.45, 10.85, 74.9, 11.35, 0.10), 0.2),
        ('seg', 'PHY_1V8A', (74.9, 11.35, 74.3, 11.95, 0.10), 0.2),
        ('seg', 'PHY_1V8A', (74.3, 11.95, 73.50, 12.55, 0.10), 0.2)],
}
gate(NEW1V8A, '1V8A relay')
add_items(NEW1V8A)
print('1V8A frags after relay:', len(fragments('PHY_1V8A', BOX)))

astar = make_astar((70.0, 80.0, 6.0, 22.0), 0.125)
rr = astar('XI', ((2,), 75.625, 18.625), (2, 75.375, 10.5), 0.10)
print('XI B drop (0.125):', 'FOUND vias=' + str(rr['vias']) if rr
      else 'NONE')
if rr:
    JI = journey_items_dense(rr, 'XI', hw=0.10)
    gate(JI, 'XI drop', skip=('XI',))
    for run in rr['runs']:
        pts = run['pts']
        print(f"  run {LAYN[run['layer']]} npts {len(pts)}: "
              + ' '.join(f"({p[0]:.2f},{p[1]:.2f})"
                         for i, p in enumerate(pts)
                         if i % 20 == 0 or i == len(pts) - 1))
    json.dump(rr, open('scratch/work/ba/design_xi_drop2.json', 'w'))
    add_items(JI)
    print('XI frags:', len(fragments('XI', BOX)))

FIN = {
    0: [('seg', 'XI', (75.375, 10.5, 75.9, 10.75, 0.10), 0.2),
        ('seg', 'XI', (75.9, 10.75, 76.2, 10.95, 0.10), 0.2),
        ('seg', 'XI', (76.2, 10.95, 76.25, 11.35, 0.10), 0.2)],
    1: [], 2: [],
}
GV = {l: [('via', 'XI', (75.375, 10.5, 0.25), 0.2)] for l in range(3)}
gate(FIN, 'XI F legs', skip=('XI',))
gate(GV, 'XI final via', skip=('XI',))
print('=== done ===')
