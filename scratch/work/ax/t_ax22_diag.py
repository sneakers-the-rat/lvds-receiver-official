import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool()
for goal in ((73.5, 5.39), (75.0, 6.83), (72.0, 3.95)):
    astar = make_astar((68.5, 76.5, 3.0, 13.5), 0.025)
    J = astar('I2C_SCL', ((0, 1, 2), 69.625, 12.625),
              (2, goal[0], goal[1]), hw=0.10)
    print(f'goal {goal}:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        print('  vias:', J['vias'], flush=True)
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
        print(f'  gate worst {worst[0]:+.3f} {L.fmt_it(worst[1])} vs '
              f'{L.fmt_it(worst[2])}', flush=True)
        break
