import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import t_ax0_pre as P
pool = load_board_pool('hw/pdlvds_rx.exp248.kicad_pcb')

# 1. SDA re-lay: blocker seg over LOS's slot band on F
blocker = ('seg', 'ZZBLOCK', (69.0, 36.5, 70.6, 36.5, 0.10), 0.35)
pool[0].append(blocker)
for _d in P._ns.values():
    _d['pool'] = pool
astar = make_astar((67.0, 74.0, 30.0, 39.0), 0.05)
J = astar('I2C_SDA', ((0,), 68.6875, 37.0), (0, 72.125, 32.625),
          hw=0.125)
print('SDA re-lay:', 'FOUND' if J else 'NONE', flush=True)
if J:
    print('  vias:', J['vias'], flush=True)
    for r in J['runs']:
        print('  run L%d' % r['layer'], r['pts'], flush=True)
    pool[0].remove(blocker)
    # rip SDA's old F chain pad->via, add the new journey
    old = chain_segs(pool, 'I2C_SDA', 0, (68.6875, 37.0), (72.125, 32.625))
    print('  old F chain segs:', len(old), flush=True)
    n = rip_items(old)
    print('  ripped:', n, flush=True)
    its = journey_items_dense(J, 'I2C_SDA', hw=0.125)
    add_items(its)
    # gate the new SDA journey against the updated pool
    worst = (9.9, None, None)
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == 'I2C_SDA':
                    continue
                m = item_margin(l, it, [o])
                if m < worst[0]:
                    worst = (m, it, o)
    print(f'  SDA gate worst {worst[0]:+.3f} {L.fmt_it(worst[1])} vs '
          f'{L.fmt_it(worst[2])}', flush=True)
    # 2. LOS full route on the re-laid pool
    astar2 = make_astar((66.0, 95.0, -1.0, 39.0), 0.05)
    J2 = astar2('CDR_LOS', ((0,), 68.6875, 36.5), (0, 92.6625, 1.75),
                hw=0.10)
    print('LOS full:', 'FOUND' if J2 else 'NONE', flush=True)
    if J2:
        print('  vias:', J2['vias'], flush=True)
        for r in J2['runs']:
            print('  run L%d' % r['layer'],
                  r['pts'][:3], '...', r['pts'][-2:], flush=True)
        its2 = journey_items_dense(J2, 'CDR_LOS', hw=0.10)
        worst = (9.9, None, None)
        for l in range(3):
            for it in its2[l]:
                for o in pool[l]:
                    if o[1] == 'CDR_LOS':
                        continue
                    m = item_margin(l, it, [o])
                    if m < worst[0]:
                        worst = (m, it, o)
        print(f'  LOS gate worst {worst[0]:+.3f} {L.fmt_it(worst[1])} vs '
              f'{L.fmt_it(worst[2])}', flush=True)
        import json
        json.dump({'sda': J, 'los': J2},
                  open('scratch/work/ax/los_design_ax89.json', 'w'))
