"""t_ax40: M4-EAST. Pool = base + stub F approach seg to W5=(67.5,5.8)
+ window via r0.25 + M1 (GND In2 re-lay) + M2 (LOL B re-lay) + M3
(+3V3D F corner re-lay), exactly as t_ax10/t_ax11 proved. Then A* B
from W5 to SCL B diagonal points. Variant B: +3V3A via (69.125,4.375)
shrunk r0.4 -> r0.3 in the pool before the A*."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

W5 = (67.5, 5.8)


def build_pool(shrink_v3a=False):
    pool = load_board_pool()
    ap = ('seg', 'I2C_SCL', (66.875, 6.75, 67.5, 5.8, 0.1), 0.2)
    pool[0].append(ap)
    wv = ('via', 'I2C_SCL', (67.5, 5.8, 0.25), 0.2)
    for l in range(3):
        pool[l].append(wv)
    # M1: GND In2 staircase re-lay (box-selected rips)
    def box_rips(net, lay, box):
        sel = []
        for it in pool[lay]:
            if it[0] != 'seg' or it[1] != net:
                continue
            d = it[2]
            if box[0] <= d[0] <= box[1] and box[2] <= d[1] <= box[3] \
                    and box[0] <= d[2] <= box[1] \
                    and box[2] <= d[3] <= box[3]:
                sel.append(it)
        n = sum(rip_items([it]) for it in sel)
        print(f'  box rips {net} L{lay}: {len(sel)} segs, {n} removals',
              flush=True)
        return sel
    box_rips('GND', 1, (65.9, 67.6, 3.9, 6.6))
    astar = make_astar((65.9, 67.6, 3.9, 6.6), 0.025)
    J = astar('GND', ((1,), 66.125, 6.375), (1, 67.375, 4.125), hw=0.10)
    assert J, 'M1 NONE'
    add_items(journey_items_dense(J, 'GND', hw=0.10))
    # M2: LOL B band re-lay (box-selected rips)
    box_rips('CDR_LOL', 2, (66.8, 68.7, 3.4, 7.3))
    astar = make_astar((66.8, 68.7, 3.4, 7.3), 0.025)
    J = astar('CDR_LOL', ((2,), 67.075, 7.125), (2, 68.62, 3.62),
              hw=0.10)
    assert J, 'M2 NONE'
    add_items(journey_items_dense(J, 'CDR_LOL', hw=0.10))
    # M3: +3V3D F corner re-lay at hw0.3
    for it in [
            ('seg', '+3V3D', (67.55, 7.25, 67.375, 6.625, 0.1), 0.25),
            ('seg', '+3V3D', (67.375, 6.625, 67.625, 6.375, 0.1), 0.25),
            ('seg', '+3V3D', (67.625, 6.375, 67.875, 6.125, 0.3), 0.25),
            ('seg', '+3V3D', (67.875, 6.125, 68.625, 6.125, 0.3), 0.25)]:
        rip_items([it])
    astar = make_astar((67.2, 68.8, 5.9, 7.4), 0.0125)
    J = astar('+3V3D', ((0,), 67.55, 7.25), (0, 68.625, 6.125), hw=0.30)
    assert J, 'M3 NONE'
    add_items(journey_items_dense(J, '+3V3D', hw=0.30))
    if shrink_v3a:
        for l in range(3):
            for i, it in enumerate(pool[l]):
                if it[0] == 'via' and it[1] == '+3V3A' and \
                        abs(it[2][0] - 69.125) < 0.01 and \
                        abs(it[2][1] - 4.375) < 0.01:
                    pool[l][i] = ('via', '+3V3A', (69.125, 4.375, 0.3),
                                  0.25)
    return pool


for shrink in (False, True):
    pool = build_pool(shrink)
    print(f'== shrink_v3a={shrink}', flush=True)
    for goal in ((71.625, 3.375), (72.375, 4.125), (73.375, 5.125),
                 (70.875, 2.625)):
        astar = make_astar((67.0, 74.5, 2.0, 7.0), 0.025)
        J = astar('I2C_SCL', ((2,), W5[0], W5[1]), (2, goal[0],
                                                    goal[1]), hw=0.10)
        print(f'  B W5 -> {goal}:', 'FOUND' if J else 'NONE',
              flush=True)
        if J:
            its = journey_items_dense(J, 'I2C_SCL', hw=0.10)
            worst = (9.9, None, None)
            for l in range(3):
                for it in its[l]:
                    for o in pool[l]:
                        if o[1] == 'I2C_SCL':
                            continue
                        m = item_margin(l, it, [o])
                        if m < worst[0]:
                            worst = (m, it, o)
            print(f'    gate worst {worst[0]:+.3f} '
                  f'{L.fmt_it(worst[1])} vs {L.fmt_it(worst[2])}',
                  flush=True)
