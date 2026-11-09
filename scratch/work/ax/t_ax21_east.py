"""t_ax21: eastern bridge test. Fresh exp241 pool; ML A* from the
stub via (69.625,12.625) to the pocket via (69.35,1.4), hw0.10,
box (68.5,75,0,13.5). If found: gate every journey item vs the pool,
report worst + the journey's vias/runs."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

pool = load_board_pool()
astar = make_astar((68.5, 75.0, 0.0, 13.5), 0.025)
J = astar('I2C_SCL', ((0, 1, 2), 69.625, 12.625), (0, 69.35, 1.4),
          hw=0.10)
# goal spec: layer tuple form is (layers, x, y) for start; goal is
# (layer, x, y) in au71 astar — try canonical: rerun variants if None
print('A* v1 (goal layer 0):', 'FOUND' if J else 'NONE', flush=True)
if not J:
    J = astar('I2C_SCL', ((0, 1, 2), 69.625, 12.625), (2, 69.35, 1.4),
              hw=0.10)
    print('A* v2 (goal layer 2):', 'FOUND' if J else 'NONE', flush=True)
if J:
    print('vias:', J['vias'], flush=True)
    for r in J['runs']:
        print('  run L? pts:', len(r), 'first', r[0], 'last', r[-1],
              flush=True)
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
    print(f'gate worst: {worst[0]:+.3f} {L.fmt_it(worst[1])} vs '
          f'{L.fmt_it(worst[2])}', flush=True)
    for l in range(3):
        print(f'  L{l}: {len(its[l])} items', flush=True)
