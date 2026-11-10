"""t_ba9: PHY_1V8A has exactly two pads (U7.29, C23.1) -- board
verified. If C23 relocates next to U7, ALL 1V8A routed copper
(notch via, B head, snake, tail) disappears. Test STP's re-lay on
that freed pool (PHY design placed, STP chain ripped, all 1V8A
routed copper ripped). A* variants S1/S2/S3 in order; exact gate
the winner and dump its geometry."""
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

# rip ALL PHY_1V8A routed copper (segs + vias, all layers)
v1 = [it for l in range(3) for it in pool[l]
      if it[1] == 'PHY_1V8A' and it[0] in ('seg', 'via')]
rip_items(v1)
print(f'1V8A routed copper ripped: {len(v1)} items; '
      f'1V8A frags now {len(fragments("PHY_1V8A", BOX))} (pads only, '
      f'expected until C23 moves)')

# STP chain rip + PHY design (as t_ba1)
ch = chain_segs(pool, 'ULPI_STP', 2, (76.10, 13.50), (77.0, 9.6))
rip_items(ch)
print(f'STP chain ripped: {len(ch)}')
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
print(f'PHY placed (loop rips {n}, tail {len(tl)}); PHY frags '
      f'{len(fragments("PHY_1V8", BOX))}; STP frags '
      f'{len(fragments("ULPI_STP", BOX))}')

astar = make_astar(DBOX, 0.05)
cands = [
    ('S1', ((2,), 76.10, 13.50), (2, 77.0, 9.6), 'design_stp_freed_s1.json'),
]
legs = None
win = None
for name, st, gl, fn in cands:
    rr = astar('ULPI_STP', st, gl, 0.10)
    print(f'{name}:', 'FOUND vias=' + str(rr['vias']) if rr else 'NONE')
    if rr:
        win = (name, rr, fn)
        break
if not win:
    legs = [it for it in pool[2] if it[1] == 'ULPI_STP' and it[0] == 'seg'
            and 75.8 < C(it)[0] < 76.4 and 13.4 < C(it)[1] < 18.0]
    rip_items(legs)
    rr = astar('ULPI_STP', ((0, 2, 1), 76.065, 17.96), (2, 77.0, 9.6), 0.10)
    print(f'S2 (legs ripped {len(legs)}):',
          'FOUND vias=' + str(rr['vias']) if rr else 'NONE')
    if rr:
        win = ('S2', rr, 'design_stp_freed_s2.json')
if not win:
    stub = [it for it in pool[0] if it[1] == 'ULPI_STP' and it[0] == 'seg']
    rip_items(stub)
    rr = astar('ULPI_STP', ((0,), 76.25, 16.4375), (2, 77.0, 9.6), 0.10)
    print(f'S3 (F stub ripped {len(stub)}):',
          'FOUND vias=' + str(rr['vias']) if rr else 'NONE')
    if rr:
        win = ('S3', rr, 'design_stp_freed_s3.json')

if win:
    name, rr, fn = win
    JI = journey_items_dense(rr, 'ULPI_STP', hw=0.10)
    pairs = []
    for l in range(3):
        for it in JI.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                m = item_margin(l, it, [o])
                if m < 0.3:
                    pairs.append((round(m, 3), LAYN[l], o[1],
                                  (round(C(it)[0], 2), round(C(it)[1], 2)),
                                  (round(C(o)[0], 2), round(C(o)[1], 2))))
    pairs.sort(key=lambda t: t[0])
    neg = sum(1 for p in pairs if p[0] < 0)
    print(f'{name} exact gate: pairs<0.3 {len(pairs)}, neg {neg}, '
          f'worst 6: {pairs[:6]}')
    add_items(JI)
    json.dump(rr, open('scratch/work/ba/' + fn, 'w'))
    print(f'{name} saved to {fn}')
    for run in rr['runs']:
        pts = run['pts']
        print(f"  run layer {run['layer']} npts {len(pts)}: "
              + ' '.join(f"({p[0]:.1f},{p[1]:.1f})"
                         for i, p in enumerate(pts)
                         if i % 15 == 0 or i == len(pts) - 1))
    print('  vias:', rr['vias'])
print('final frags: PHY', len(fragments('PHY_1V8', BOX)),
      'STP', len(fragments('ULPI_STP', BOX)),
      '1V8A', len(fragments('PHY_1V8A', BOX)),
      'CK', len(fragments('ULPI_CK', BOX)),
      'XI', len(fragments('XI', BOX)),
      'XO', len(fragments('XO', BOX)))
print('=== done ===')
