import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
from t_ax40_m4east import build_pool
pool = build_pool(False)
for goal, gl in (((78.125, 8.375), 1), ((79.125, 8.375), 1),
                 ((77.38, 9.12), 2), ((76.5, 9.87), 2)):
    astar = make_astar((67.0, 80.5, 3.0, 13.0), 0.025)
    J = astar('I2C_SCL', ((0, 1, 2), 67.5, 5.8), (gl, goal[0], goal[1]),
              hw=0.10)
    print(f'W5 -> {goal} L{gl}:', 'FOUND' if J else 'NONE', flush=True)
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
