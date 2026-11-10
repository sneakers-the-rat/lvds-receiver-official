"""t_az18: v8 coupled district configuration (model-level).
Re-lays (all attach at verified joints):
 - PHY_1V8A notch: via (75.737,10.75)->(75.30,10.30); F stub from
   surviving joint (75.72,11.0): ->(75.45,10.50)->(75.30,10.30);
   B head seg -> (75.30,10.30)->(75.30,11.35) rejoin.
 - XO F escape: rip from joint (76.75,11.125); new
   (76.75,11.125)->(76.62,10.80)->(76.62,9.95)->(75.90,9.70) rejoin.
 - ULPI_STP B bottom: rip from joint (76.0,11.85) to via (77,9.6);
   new (76.0,11.85)->(76.55,11.50)->(76.80,10.40)->(76.90,9.70)
   ->(77.0,9.6).
 - PHY_1V8 B loop east: rip chain (77.25,10.75)->(77.8,16.2);
   new (77.25,10.75)->(77.42,10.55)->(77.30,11.10)->(77.30,15.10)
   ->(77.8,16.2).
Guards: fragment counts of re-laid nets unchanged. Then exact-gate
all new items, then A* XI and PHY (0.05 grid), exact-gate journeys.
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)


def seg(net, x1, y1, x2, y2, hw=0.10, clr=0.2):
    return ('seg', net, (x1, y1, x2, y2, hw), clr)


def via(net, x, y, r=0.25, clr=0.2):
    return ('via', net, (x, y, r), clr)


def gate_items(items_by_layer, label, thresh=0.30):
    worst = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                m = item_margin(l, it, [o])
                if m < thresh:
                    worst.append((round(m, 3), l, it, o))
    worst.sort(key=lambda t: t[0])
    print(f'{label}: {len(worst)} pairs < {thresh}; worst 6:')
    for w in worst[:6]:
        print('   ', w)
    return worst


pool = load_board_pool(BOARD)
NETS = ['ULPI_STP', 'PHY_1V8A', 'XO', 'PHY_1V8', 'XI']
base = {n: len(fragments(n, BOX)) for n in NETS}
print('faithful fragments:', base)

# --- 1V8A notch move ---
rip_items([it for l in range(3) for it in pool[l]
           if it[1] == 'PHY_1V8A' and it[0] == 'via'
           and abs(it[2][0] - 75.737) < 0.01
           and abs(it[2][1] - 10.75) < 0.01])
rip_items([it for it in pool[0] if it[1] == 'PHY_1V8A'
           and it[0] == 'seg' and abs(it[2][0] - 75.72) < 0.01
           and abs(it[2][1] - 11.0) < 0.01 and it[2][3] < 11.0])
rip_items([it for it in pool[2] if it[1] == 'PHY_1V8A'
           and it[0] == 'seg' and abs(it[2][0] - 75.737) < 0.01
           and abs(it[2][1] - 10.75) < 0.01])
N1 = {0: [via('PHY_1V8A', 75.30, 10.30, 0.25, 0.25),
          seg('PHY_1V8A', 75.72, 11.0, 75.45, 10.50, 0.10, 0.25),
          seg('PHY_1V8A', 75.45, 10.50, 75.30, 10.30, 0.10, 0.25)],
      1: [via('PHY_1V8A', 75.30, 10.30, 0.25, 0.25)],
      2: [via('PHY_1V8A', 75.30, 10.30, 0.25, 0.25),
          seg('PHY_1V8A', 75.30, 10.30, 75.30, 11.35, 0.10, 0.25)]}
add_items(N1)

# --- XO F escape jog east ---
xo_rip = []
for it in list(pool[0]):
    if it[1] != 'XO' or it[0] != 'seg':
        continue
    cx, cy = C(it)
    d = it[2]
    if (76.2 < cx < 76.9 and 10.15 < cy < 11.3) or \
       (75.15 < cx < 76.6 and 9.55 < cy < 10.3 and
            min(d[0], d[2]) > 75.15):
        xo_rip.append(it)
rip_items(xo_rip)
print('XO ripped segs:', len(xo_rip))
N2 = {0: [seg('XO', 76.75, 11.125, 76.62, 10.80),
          seg('XO', 76.62, 10.80, 76.62, 9.95),
          seg('XO', 76.62, 9.95, 75.90, 9.70)], 1: [], 2: []}
add_items(N2)

# --- STP B bottom re-lay ---
try:
    ch = chain_segs(pool, 'ULPI_STP', 2, (76.0, 11.85), (77.0, 9.6))
    rip_items(ch)
    print('STP bottom ripped segs:', len(ch))
except SystemExit as e:
    print('STP chain FAILED', e)
N3 = {0: [], 1: [], 2: [seg('ULPI_STP', 76.0, 11.85, 76.55, 11.50),
                       seg('ULPI_STP', 76.55, 11.50, 76.80, 10.40),
                       seg('ULPI_STP', 76.80, 10.40, 76.90, 9.70),
                       seg('ULPI_STP', 76.90, 9.70, 77.0, 9.6)]}
add_items(N3)

# --- PHY B loop east ---
try:
    ch = chain_segs(pool, 'PHY_1V8', 2, (77.55, 10.35), (77.8, 16.2))
    rip_items(ch)
    print('PHY loop ripped segs (from 77.55,10.35):', len(ch))
except SystemExit as e:
    print('PHY chain FAILED', e)
rip_items([it for it in pool[2] if it[1] == 'PHY_1V8' and it[0] == 'seg'
           and abs(it[2][0] - 77.25) < 0.01 and abs(it[2][1] - 10.75) < 0.01
           and abs(it[2][2] - 77.55) < 0.01 and abs(it[2][3] - 10.35) < 0.01])
N4 = {0: [], 1: [], 2: [seg('PHY_1V8', 77.25, 10.75, 77.42, 10.55, 0.10, 0.25),
                       seg('PHY_1V8', 77.42, 10.55, 77.30, 11.10, 0.10, 0.25),
                       seg('PHY_1V8', 77.30, 11.10, 77.30, 15.10, 0.15, 0.25),
                       seg('PHY_1V8', 77.30, 15.10, 77.80, 16.20, 0.10, 0.25)]}
add_items(N4)

now = {n: len(fragments(n, BOX)) for n in NETS}
print('v8 fragments:', now, '(faithful:', base, ')')
for lbl, NN in [('notch', N1), ('XO jog', N2), ('STP bottom', N3),
                ('PHY loop', N4)]:
    gate_items(NN, f'{lbl} gate')

astar = make_astar((70.0, 88.0, 8.0, 23.0), 0.05)
for net, goals in [('XI', [(2, 75.625, 18.625), (0, 75.72, 18.73)]),
                   ('PHY_1V8', [(0, 72.02, 18.0)])]:
    src = ((0,), 76.25, 11.562) if net == 'XI' else ((2,), 77.8, 16.2)
    for (gl, gx, gy) in goals:
        r = astar(net, src, (gl, gx, gy), 0.10 if net == 'XI' else 0.10)
        print(f'{net} -> L{gl} ({gx},{gy}):',
              f'FOUND vias={r["vias"]}' if r else 'none')
        if r:
            for rn in r['runs']:
                print(f"   L{rn['layer']} {len(rn['pts'])} pts "
                      f"{rn['pts'][0]} -> {rn['pts'][-1]}")
            gate_items(journey_items_dense(r, net, hw=0.10),
                       f'{net} journey gate')
            break
print('=== done ===')
