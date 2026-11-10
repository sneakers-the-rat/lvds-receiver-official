"""t_ba22: STP wholesale re-plan on the TRUE exp252 pool
(PHY as-built, 1V8A snake present). Rip all STP items; A*
U7.13 (76.25,16.4375) F -> U6.26 (71.338,2.25) F. Gate the
winner; report whether the southern B chain district
(x[75.8,77.6] y[7.5,13.6]) is vacated; re-gate C22's GND
via (76.4,9.0) + dogleg track in the new configuration."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}

pool = load_board_pool(BOARD)
vic = [it for l in range(3) for it in pool[l]
       if it[1] == 'ULPI_STP' and it[0] in ('seg', 'via')]
rip_items(vic)
print(f'STP ripped {len(vic)} model items; frags '
      f'{len(fragments("ULPI_STP", BOX))}')

astar = make_astar((66.0, 84.0, -2.0, 22.0), 0.05)
rr = astar('ULPI_STP', ((0,), 76.25, 16.4375), (0, 71.338, 2.25), 0.10)
print('STP re-plan:', 'FOUND vias=' + str(rr['vias']) if rr else 'NONE')
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
    print(f'gate: pairs<0.1 {len(pairs)}, neg {neg}, worst 6: {pairs[:6]}')
    # southern chain district occupancy by the new route
    occ = []
    for l in range(3):
        for it in JI.get(l, []):
            cc = C(it)
            if 75.8 <= cc[0] <= 77.6 and 7.5 <= cc[1] <= 13.6:
                occ.append((LAYN[l], it[0],
                            (round(cc[0], 2), round(cc[1], 2))))
    print(f'new STP items in southern chain district: {len(occ)} {occ[:8]}')
    for run in rr['runs']:
        pts = run['pts']
        print(f"  run {LAYN[run['layer']]} npts {len(pts)}: "
              + ' '.join(f"({p[0]:.1f},{p[1]:.1f})"
                         for i, p in enumerate(pts)
                         if i % 20 == 0 or i == len(pts) - 1))
    print('  vias:', rr['vias'])
    if neg == 0:
        json.dump(rr, open('scratch/work/ba/design_stp_replan.json', 'w'))
        add_items(JI)
        print('SAVED design_stp_replan.json; STP frags',
              len(fragments('ULPI_STP', BOX)))
        # re-gate C22 GND tie in the new configuration
        def gate_via(x, y, net='GND'):
            it = ('via', net, (x, y, 0.25), 0.2)
            w, wo = 9.9, None
            for l in range(3):
                for o in pool[l]:
                    if o[1] == net:
                        continue
                    cc = C(o)
                    if abs(cc[0] - x) > 3 or abs(cc[1] - y) > 3:
                        continue
                    m = item_margin(l, it, [o])
                    if m < w:
                        w, wo = m, (LAYN[l], o[1])
            return w, wo
        def gate_track(l, net, x1, y1, x2, y2, hw=0.10):
            it = ('seg', net, (x1, y1, x2, y2, hw), 0.2)
            w, wo = 9.9, None
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < w:
                    w, wo = m, o[1]
            return w, wo
        gv, wo = gate_via(76.4, 9.0)
        g1, w1 = gate_track(0, 'GND', 77.5, 9.22, 77.0, 9.15)
        g2, w2 = gate_track(0, 'GND', 77.0, 9.15, 76.4, 9.0)
        print(f'C22 GND tie now: via (76.4,9.0) {gv:+.3f} vs {wo}; '
              f'dogleg legs {g1:+.3f} vs {w1} / {g2:+.3f} vs {w2}')
print('=== done ===')
