"""t_az10: A* probes for all three nets on scenario pools.
Scenarios reuse t_az9's fence-move definitions (imported by exec).
S3 = notch move + XO re-lay + S1 re-lay. S4 = S3 + STP B staircase
rip (pocket band). Also S5 = S4 + STP B leg north rip (y13.5-18.1)
+ STP In2 ride added (the PHY F1 re-lay), and S6 = S5 + PHY B
loop vertical moved east x76.95 -> x77.45.
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


def apply_scen(pool, name):
    if name in ('S3', 'S4', 'S5', 'S6'):
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
        add_items({0: [via('PHY_1V8A', 75.65, 10.60, 0.25, 0.25),
                       seg('PHY_1V8A', 75.75, 11.562, 75.65, 10.60, 0.10, 0.25)],
                   1: [via('PHY_1V8A', 75.65, 10.60, 0.25, 0.25)],
                   2: [via('PHY_1V8A', 75.65, 10.60, 0.25, 0.25),
                       seg('PHY_1V8A', 75.65, 10.60, 75.30, 11.35, 0.10, 0.25)]})
        rip_items([it for it in pool[0]
                   if it[1] == 'XO' and it[0] == 'seg'
                   and 76.2 < C(it)[0] < 77.0 and 10.3 < C(it)[1] < 11.7])
        rip_items([it for it in pool[0]
                   if it[1] == 'XO' and it[0] == 'seg'
                   and 75.8 < C(it)[0] < 76.6 and 10.3 < C(it)[1] < 11.0])
        add_items({0: [seg('XO', 76.75, 11.562, 76.725, 10.90),
                       seg('XO', 76.725, 10.90, 76.00, 10.90),
                       seg('XO', 76.00, 10.90, 75.25, 9.60)]})
        rip_items([it for it in pool[1]
                   if it[1] == '+3V3A' and it[0] == 'seg'
                   and abs(it[2][0] - 77.125) < 0.01
                   and abs(it[2][1] - 13.125) < 0.01
                   and abs(it[2][2] - 76.625) < 0.01
                   and abs(it[2][3] - 10.25) < 0.01])
        add_items({1: [seg('+3V3A', 77.125, 13.125, 77.55, 11.60, 0.10, 0.25),
                       seg('+3V3A', 77.55, 11.60, 77.20, 10.50, 0.10, 0.25),
                       seg('+3V3A', 77.20, 10.50, 76.625, 10.25, 0.10, 0.25)]})
    if name in ('S4', 'S5', 'S6'):
        rip_items([it for it in pool[2]
                   if it[1] == 'ULPI_STP' and it[0] == 'seg'
                   and 75.9 < C(it)[0] < 76.6 and 10.0 < C(it)[1] < 13.6])
    if name in ('S5', 'S6'):
        # F1: STP B leg y13.5-18.1 -> In2 ride
        rip_items([it for it in pool[2]
                   if it[1] == 'ULPI_STP' and it[0] == 'seg'
                   and 75.9 < C(it)[0] < 76.6 and 13.4 < C(it)[1] < 18.3])
        add_items({1: [seg('ULPI_STP', 76.065, 17.96, 76.20, 14.20, 0.10, 0.2)],
                   0: [via('ULPI_STP', 76.20, 14.20, 0.25, 0.2)],
                   2: [via('ULPI_STP', 76.20, 14.20, 0.25, 0.2),
                       seg('ULPI_STP', 76.20, 14.20, 76.15, 13.50, 0.10, 0.2)]})
        add_items({1: [via('ULPI_STP', 76.20, 14.20, 0.25, 0.2)]})
    if name == 'S6':
        # PHY B loop vertical x76.95 -> x77.45 (y11.05-14.988) + arms
        rip_items([it for it in pool[2]
                   if it[1] == 'PHY_1V8' and it[0] == 'seg'
                   and abs(it[2][0] - 76.95) < 0.01
                   and abs(it[2][2] - 76.95) < 0.01])
        rip_items([it for it in pool[2]
                   if it[1] == 'PHY_1V8' and it[0] == 'seg'
                   and abs(it[2][0] - 76.95) < 0.01
                   and abs(it[2][1] - 14.988) < 0.01])
        rip_items([it for it in pool[2]
                   if it[1] == 'PHY_1V8' and it[0] == 'seg'
                   and abs(it[2][0] - 77.45) < 0.01
                   and abs(it[2][1] - 10.10) < 0.01])
        add_items({2: [seg('PHY_1V8', 77.45, 11.05, 77.45, 14.988, 0.15, 0.25),
                       seg('PHY_1V8', 77.45, 14.988, 77.80, 16.20, 0.15, 0.25),
                       seg('PHY_1V8', 77.45, 11.05, 77.25, 10.75, 0.10, 0.25)]})


def probe(net, box, start, goals, hw=0.10):
    astar = make_astar(box, 0.125)
    for (gl, gx, gy) in goals:
        r = astar(net, start, (gl, gx, gy), hw)
        print(f'    {net} -> L{gl} ({gx},{gy}):',
              f'FOUND vias={r["vias"]}' if r else 'none')


XI_BOX = (70.0, 88.0, 8.0, 23.0)
XI_START = ((0,), 76.25, 11.562)
XI_GOALS = [(2, 75.625, 18.625), (0, 75.72, 18.73), (2, 78.375, 21.125)]
PHY_BOX = (68.0, 82.0, 6.0, 22.0)
PHY_START = ((0,), 72.02, 18.0)
PHY_GOALS = [(2, 77.8, 16.2), (0, 77.25, 16.4375), (2, 76.95, 13.0)]
RST_BOX = (68.0, 84.0, 0.0, 20.0)
RST_START = ((0,), 74.25, 16.4375)
RST_GOALS = [(0, 74.75, 4.662), (2, 74.75, 4.662), (1, 74.75, 4.662)]

for name in ('S3', 'S4', 'S5', 'S6'):
    print(f'== {name}')
    pool = load_board_pool(BOARD)
    apply_scen(pool, name)
    probe('XI', XI_BOX, XI_START, XI_GOALS)
    probe('PHY_1V8', PHY_BOX, PHY_START, PHY_GOALS)
    probe('USB_RST', RST_BOX, RST_START, RST_GOALS)
print('=== done ===')
