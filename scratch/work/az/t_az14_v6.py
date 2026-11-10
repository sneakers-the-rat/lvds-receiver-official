"""t_az14: scenario v6 for XI + PHY.
Re-lays (model level):
 - PHY_1V8A notch via (75.737,10.75) -> (75.25,10.40); F stub and
   B rejoin seg re-laid.
 - XO F escape threaded east/south of the XI dive (76.0,10.625).
 - ULPI_STP B leg+staircase (y11.3-16.0) jogged east to x76.45-76.55
   so XI can ride B west of it under the EP, crossing ULPI_CK's
   In2 y13.5 line on B.
CK, +3V3A, PHY loop untouched. Verify: fragments() counts for the
re-laid nets unchanged; A* for XI and PHY_1V8.
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'


def seg(net, x1, y1, x2, y2, hw=0.10, clr=0.2):
    return ('seg', net, (x1, y1, x2, y2, hw), clr)


def via(net, x, y, r=0.25, clr=0.2):
    return ('via', net, (x, y, r), clr)


def apply_v6(pool):
    # --- PHY_1V8A notch move ---
    rip_items([it for l in range(3) for it in pool[l]
               if it[1] == 'PHY_1V8A' and it[0] == 'via'
               and abs(it[2][0] - 75.737) < 0.01
               and abs(it[2][1] - 10.75) < 0.01])
    rip_items([it for it in pool[0]
               if it[1] == 'PHY_1V8A' and it[0] == 'seg'
               and C(it)[0] > 75.6 and C(it)[1] > 10.6])
    rip_items([it for it in pool[2]
               if it[1] == 'PHY_1V8A' and it[0] == 'seg'
               and abs(it[2][0] - 75.737) < 0.01
               and abs(it[2][1] - 10.75) < 0.01])
    add_items({0: [via('PHY_1V8A', 75.25, 10.40, 0.25, 0.25),
                   seg('PHY_1V8A', 75.75, 11.562, 75.50, 11.00, 0.10, 0.25),
                   seg('PHY_1V8A', 75.50, 11.00, 75.25, 10.40, 0.10, 0.25)],
               1: [via('PHY_1V8A', 75.25, 10.40, 0.25, 0.25)],
               2: [via('PHY_1V8A', 75.25, 10.40, 0.25, 0.25),
                   seg('PHY_1V8A', 75.25, 10.40, 75.30, 11.35, 0.10, 0.25)]})
    # --- XO F escape re-lay ---
    rip_items([it for it in pool[0]
               if it[1] == 'XO' and it[0] == 'seg'
               and 76.2 < C(it)[0] < 77.0 and 10.3 < C(it)[1] < 11.7])
    rip_items([it for it in pool[0]
               if it[1] == 'XO' and it[0] == 'seg'
               and 75.8 < C(it)[0] < 76.6 and 10.3 < C(it)[1] < 11.0])
    add_items({0: [seg('XO', 76.75, 11.562, 76.725, 10.90),
                   seg('XO', 76.725, 10.90, 76.45, 10.90),
                   seg('XO', 76.45, 10.90, 76.50, 10.30),
                   seg('XO', 76.50, 10.30, 75.90, 9.90),
                   seg('XO', 75.90, 9.90, 75.25, 9.60)]})
    # --- ULPI_STP B jog east ---
    rip_items([it for it in pool[2]
               if it[1] == 'ULPI_STP' and it[0] == 'seg'
               and 75.9 < C(it)[0] < 76.6 and 11.3 < C(it)[1] < 16.0])
    add_items({2: [seg('ULPI_STP', 76.27, 16.20, 76.55, 15.00),
                   seg('ULPI_STP', 76.55, 15.00, 76.55, 13.00),
                   seg('ULPI_STP', 76.55, 13.00, 76.45, 11.80),
                   seg('ULPI_STP', 76.45, 11.80, 76.30, 11.30)]})


def frag_count(pool, net, box=(58.0, 96.0, -30.0, 34.0)):
    return len(fragments(net, box))


pool = load_board_pool(BOARD)
base = {n: frag_count(pool, n)
        for n in ('ULPI_STP', 'PHY_1V8A', 'XO', 'PHY_1V8', 'XI')}
print('faithful fragments:', base)
apply_v6(pool)
now = {n: frag_count(pool, n)
       for n in ('ULPI_STP', 'PHY_1V8A', 'XO', 'PHY_1V8', 'XI')}
print('v6 fragments:', now)

astar = make_astar((70.0, 88.0, 8.0, 23.0), 0.125)
for (gl, gx, gy) in [(2, 75.625, 18.625), (0, 75.72, 18.73),
                     (2, 78.375, 21.125)]:
    r = astar('XI', ((0,), 76.25, 11.562), (gl, gx, gy), 0.10)
    print(f'XI -> L{gl} ({gx},{gy}):',
          f'FOUND vias={r["vias"]}' if r else 'none')
    if r:
        for rn in r['runs']:
            print(f"   L{rn['layer']} {len(rn['pts'])} pts "
                  f"{rn['pts'][0]} -> {rn['pts'][-1]}")
astar2 = make_astar((68.0, 82.0, 6.0, 22.0), 0.125)
for (gl, gx, gy) in [(2, 77.8, 16.2), (0, 77.25, 16.4375), (2, 76.95, 13.0)]:
    r = astar2('PHY_1V8', ((0,), 72.02, 18.0), (gl, gx, gy), 0.10)
    print(f'PHY -> L{gl} ({gx},{gy}):',
          f'FOUND vias={r["vias"]}' if r else 'none')
print('=== done ===')
