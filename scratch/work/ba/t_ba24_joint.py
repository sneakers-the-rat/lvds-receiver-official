"""t_ba24: joint model assembly for exp253.
- rip STP southern/mid items (t_ba23 rule)
- blockers reserving C22's GND via site (76.4,9.0) r0.5 and
  pushing STP's F-transition off (78.3,1.85) r0.4
- STP A* legs-end (76.10,13.50) -> (70.25,-2.20); exact gate
- then gate C22 north design in the resulting pool: pad1 hop
  (77.50,10.18)->(77.90,10.08) F; GND via (76.4,9.0); GND
  track (77.5,9.22)->(77.0,9.15)->(76.4,9.0) F."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)

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
print(f'ripped {len(rip)} southern/mid STP items')

BLK = {0: [], 1: [], 2: []}
for l in range(3):
    BLK[l].append(('via', 'ZZBLK', (76.4, 9.0, 0.50), 0.2))
    BLK[l].append(('via', 'ZZBLK', (78.3, 1.85, 0.40), 0.2))
add_items(BLK)

astar = make_astar((64.0, 84.0, -6.0, 22.0), 0.05)
rr = astar('ULPI_STP', ((2,), 76.10, 13.50), (2, 70.25, -2.20), 0.10)
print('STP re-plan (blocked):',
      'FOUND vias=' + str(rr['vias']) if rr else 'NONE')
if rr:
    JI = journey_items_dense(rr, 'ULPI_STP', hw=0.10)
    pairs = []
    for l in range(3):
        for it in JI.get(l, []):
            for o in pool[l]:
                if o[1] in ('ULPI_STP', 'ZZBLK'):
                    continue
                m = item_margin(l, it, [o])
                if m < 0.1:
                    pairs.append((round(m, 3), LAYN[l], o[1],
                                  (round(C(it)[0], 2), round(C(it)[1], 2)),
                                  (round(C(o)[0], 2), round(C(o)[1], 2))))
    pairs.sort(key=lambda t: t[0])
    neg = sum(1 for p in pairs if p[0] < 0)
    print(f'STP gate (excl blockers): neg {neg}, worst 6: {pairs[:6]}')
    for run in rr['runs']:
        pts = run['pts']
        print(f"  run {LAYN[run['layer']]} npts {len(pts)}: "
              + ' '.join(f"({p[0]:.1f},{p[1]:.1f})"
                         for i, p in enumerate(pts)
                         if i % 20 == 0 or i == len(pts) - 1))
    print('  vias:', rr['vias'])
    if neg == 0:
        json.dump(rr, open('scratch/work/ba/design_stp_south2.json', 'w'))
        add_items(JI)
        print('STP placed; frags', len(fragments('ULPI_STP', BOX)))

# remove blockers, gate the C22 design
rip_items([it for l in range(3) for it in BLK[l]])


def gate_track(l, net, x1, y1, x2, y2, hw=0.10):
    it = ('seg', net, (x1, y1, x2, y2, hw),
          0.25 if net in ('PHY_1V8',) else 0.2)
    w, wo = 9.9, None
    for o in pool[l]:
        if o[1] == net:
            continue
        cc = C(o)
        if abs(cc[0] - (x1 + x2) / 2) > 4 or abs(cc[1] - (y1 + y2) / 2) > 4:
            continue
        m = item_margin(l, it, [o])
        if m < w:
            w, wo = m, o[1]
    return w, wo


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


g, w = gate_track(0, 'PHY_1V8', 77.50, 10.18, 77.90, 10.08)
print(f'C22 pad1 hop: {g:+.3f} vs {w}')
gv, wo = gate_via(76.4, 9.0)
print(f'C22 GND via (76.4,9.0): {gv:+.3f} vs {wo}')
g1, w1 = gate_track(0, 'GND', 77.5, 9.22, 77.0, 9.15)
g2, w2 = gate_track(0, 'GND', 77.0, 9.15, 76.4, 9.0)
print(f'C22 GND track legs: {g1:+.3f} vs {w1} / {g2:+.3f} vs {w2}')
gv2, wo2 = gate_via(76.15, 8.55)
g3, w3 = gate_track(0, 'GND', 77.5, 9.22, 76.15, 8.55)
print(f'alt GND via (76.15,8.55): {gv2:+.3f} vs {wo2}; '
      f'direct track {g3:+.3f} vs {w3}')
print('=== done ===')
