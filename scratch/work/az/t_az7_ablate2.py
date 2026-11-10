"""t_az7: second ablation round.
- DM_PHY via coordinate check (R-A's via rip matched 0 entries).
- XI X-H: mega-rip of the pocket + north column (all non-XI segs/vias
  with centre in the boxes, U7 pads kept) -> does ANY route exist?
- XI X-I: all four named fences ripped at once (STP B leg y13.5-18.1,
  STP B staircase y10-13.5, notch via, XO F escape, +3V3A In2 web).
- RST R-H: mega-rip north box x[73,77] y[15,20.5] (non-RST segs/vias).
- RST R-I: from the TARGET side: A* (74.75,3.4) F/B/In2 -> U7.9 with
  DM loop+via properly ripped (by centre predicate).
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'

pool = load_board_pool(BOARD)
print('DM_PHY vias in pool:')
for l in range(3):
    for it in pool[l]:
        if it[1] == 'DM_PHY' and it[0] == 'via':
            print('   L%d' % l, it)
print('DM_PHY F items near the loop:')
for it in pool[0]:
    if it[1] == 'DM_PHY':
        print('   ', it)


def rip_pred(pool, pred, label):
    its = []
    for l in range(3):
        for it in pool[l]:
            if pred(l, it):
                its.append(it)
    n = rip_items(its)
    print(f'    ripped {label}: {len(its)} entries, {n} removals')
    return its


def probe(net, box, start, goals, hw=0.10):
    astar = make_astar(box, 0.125)
    for (gl, gx, gy) in goals:
        r = astar(net, start, (gl, gx, gy), hw)
        print(f'    {net} -> L{gl} ({gx},{gy}):',
              f'FOUND vias={r["vias"]}' if r else 'none')


def ctr_in(x0, x1, y0, y1):
    def f(l, it):
        p = C(it)
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    return f


XI_BOX = (70.0, 88.0, 8.0, 23.0)
XI_START = ((0,), 76.25, 11.562)
XI_GOALS = [(2, 75.625, 18.625), (0, 75.72, 18.73), (2, 78.375, 21.125)]
RST_BOX = (68.0, 84.0, 0.0, 20.0)
RST_START = ((0,), 74.25, 16.4375)
RST_GOALS = [(0, 74.75, 4.662), (2, 74.75, 4.662), (1, 74.75, 4.662)]

print('== X-H: mega-rip pocket + column (non-XI segs/vias)')
pool = load_board_pool(BOARD)
rip_pred(pool, lambda l, it: it[1] != 'XI' and it[0] in ('seg', 'via')
         and ctr_in(75.3, 77.1, 10.0, 12.3)(l, it), 'pocket rip')
rip_pred(pool, lambda l, it: it[1] != 'XI' and it[0] in ('seg', 'via')
         and ctr_in(75.6, 76.6, 12.3, 18.3)(l, it), 'column rip')
probe('XI', XI_BOX, XI_START, XI_GOALS)

print('== X-I: four fences ripped')
pool = load_board_pool(BOARD)
rip_pred(pool, lambda l, it: it[1] == 'ULPI_STP' and l == 2
         and ctr_in(75.7, 76.6, 10.0, 18.3)(l, it), 'STP B column+stair')
rip_pred(pool, lambda l, it: it[1] == 'PHY_1V8A' and it[0] == 'via'
         and abs(it[2][0] - 75.7375) < 0.01 and abs(it[2][1] - 10.75) < 0.01,
         'notch via')
rip_pred(pool, lambda l, it: it[1] == 'XO' and l == 0
         and ctr_in(76.2, 77.0, 10.3, 11.7)(l, it), 'XO F esc')
rip_pred(pool, lambda l, it: it[1] == '+3V3A' and l == 1
         and ctr_in(76.2, 78.6, 9.8, 16.6)(l, it), '+3V3A In2 web')
probe('XI', XI_BOX, XI_START, XI_GOALS)

print('== R-H: mega-rip north box (non-RST segs/vias)')
pool = load_board_pool(BOARD)
rip_pred(pool, lambda l, it: it[1] != 'USB_RST' and it[0] in ('seg', 'via')
         and ctr_in(73.0, 77.0, 15.0, 20.5)(l, it), 'north rip')
probe('USB_RST', RST_BOX, RST_START, RST_GOALS)

print('== R-I: DM loop+via ripped by centre; target-side goals')
pool = load_board_pool(BOARD)
rip_pred(pool, lambda l, it: it[1] == 'DM_PHY'
         and ctr_in(73.2, 74.6, 15.2, 19.6)(l, it), 'DM box all layers')
probe('USB_RST', RST_BOX, RST_START, RST_GOALS)
print('  reverse: from U6.40 F to corridor head + U7.9:')
probe('USB_RST', RST_BOX, ((0,), 74.75, 4.662),
      [(0, 74.75, 3.4), (2, 74.75, 3.4), (0, 74.25, 16.4375)])
print('=== done ===')
