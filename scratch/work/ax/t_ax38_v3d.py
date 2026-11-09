import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
from t_ax37_south2 import STUB, FEED
pool = load_board_pool()
for it in STUB + FEED:
    rip_items([it])
for net, px in (('I2C_SCL', 69.425), ('+3V3D', 71.075)):
    for p in [it for it in pool[0] if it[0] == 'pad' and it[1] == net
              and abs(it[2][0] - px) < 0.01
              and abs(it[2][1] - 12.75) < 0.01]:
        rip_items([p])
pool[0].append(('seg', '+3V3D', (70.625, 12.375, 70.875, 12.625, 0.1),
                0.25))
p2 = (69.325, -1.75)
pool[0].append(('pad', '+3V3D', (p2[0], p2[1], 0.4, 0.475, 0.0), 0.25))
for goal, gl, box in (
        ((72.875, 3.375), 2, (66.0, 74.0, -3.0, 4.5)),
        ((72.875, 3.375), 1, (66.0, 74.0, -3.0, 4.5)),
        ((74.875, 1.875), 0, (66.0, 76.0, -3.0, 4.5)),
        ((71.338, -0.25), 0, (66.0, 74.0, -3.0, 4.5))):
    astar = make_astar(box, 0.025)
    J = astar('+3V3D', ((0,), p2[0], p2[1]), (gl, goal[0], goal[1]),
              hw=0.10)
    print(f'goal {goal} L{gl}:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        print('   vias:', J['vias'], flush=True)
        its = journey_items_dense(J, '+3V3D', hw=0.10)
        worst = (9.9, None, None)
        for l in range(3):
            for it in its[l]:
                for o in pool[l]:
                    if o[1] == '+3V3D':
                        continue
                    m = item_margin(l, it, [o])
                    if m < worst[0]:
                        worst = (m, it, o)
        print(f'   gate worst {worst[0]:+.3f} {L.fmt_it(worst[1])} vs '
              f'{L.fmt_it(worst[2])}', flush=True)
