import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool()
for goal, gl in (((77.38, 9.12), 2), ((78.12, 8.38), 2),
                 ((78.125, 8.375), 1), ((76.5, 9.87), 2)):
    astar = make_astar((68.5, 79.5, 0.5, 13.5), 0.025)
    J = astar('I2C_SCL', ((0, 1, 2), 69.625, 12.625), (gl, goal[0],
                                                      goal[1]), hw=0.10)
    print(f'island via -> {goal} L{gl}:', 'FOUND' if J else 'NONE',
          flush=True)
    if J:
        print('   vias:', J['vias'], flush=True)
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
        print(f'   gate worst {worst[0]:+.3f} {L.fmt_it(worst[1])} vs '
              f'{L.fmt_it(worst[2])}', flush=True)
