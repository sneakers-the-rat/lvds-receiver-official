import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp248.kicad_pcb')
astar = make_astar((66.0, 95.0, -1.0, 39.0), 0.05)
J = astar('CDR_LOS', ((0,), 68.6875, 36.5), (0, 92.6625, 1.75),
          hw=0.10)
print('LOS A*:', 'FOUND' if J else 'NONE', flush=True)
if J:
    print('vias:', J['vias'], flush=True)
    its = journey_items_dense(J, 'CDR_LOS', hw=0.10)
    worst = (9.9, None, None)
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == 'CDR_LOS':
                    continue
                m = item_margin(l, it, [o])
                if m < worst[0]:
                    worst = (m, it, o)
    print(f'gate worst {worst[0]:+.3f} {L.fmt_it(worst[1])} vs '
          f'{L.fmt_it(worst[2])}', flush=True)
