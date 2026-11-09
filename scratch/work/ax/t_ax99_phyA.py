import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
astar = make_astar((67.0, 80.0, 7.0, 18.0), 0.05)
J = astar('PHY_1V8A', ((0,), 69.975, 14.75), (0, 75.75, 11.5625), hw=0.10)
print('PHY A* direct:', 'FOUND' if J else 'NONE', flush=True)
if J:
    print('vias:', J['vias'], flush=True)
    its = journey_items_dense(J, 'PHY_1V8A', hw=0.10)
    worst = (9.9, None, None)
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == 'PHY_1V8A':
                    continue
                m = item_margin(l, it, [o])
                if m < worst[0]:
                    worst = (m, it, o)
    print(f'gate worst {worst[0]:+.3f} {L.fmt_it(worst[1])} vs '
          f'{L.fmt_it(worst[2])}', flush=True)
