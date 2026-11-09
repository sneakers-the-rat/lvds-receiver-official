"""t_ax18: replay via+M1+M2, then print B-layer binders for SCL at
points along y=5.75 (x68..70.6) and the eastern channel (71.1, 3.4..5),
and goal (69.35,1.4)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

W = (67.5, 5.8)
pool = load_board_pool()
via = ('via', 'I2C_SCL', (W[0], W[1], 0.25), 0.2)
add_items({0: [via], 2: [via]})
pool[1].append(via)
pool[1].append(('seg', 'I2C_SCL', (66.875, 6.75, W[0], W[1], 0.10), 0.2))
rip = chain_segs(pool, 'GND', 1, (66.375, 6.125), (67.375, 4.125))
rip_items(rip)
astar = make_astar((65.4, 68.2, 3.4, 7.0), 0.025)
J = astar('GND', ((1,), 66.375, 6.125), (1, 67.375, 4.125), hw=0.125)
add_items(journey_items_dense(J, 'GND', hw=0.125))
rip = chain_segs(pool, 'CDR_LOL', 2, (67.625, 6.625), (68.375, 4.125))
rip_items(rip)
astar = make_astar((66.2, 70.6, 3.0, 8.0), 0.025)
J = astar('CDR_LOL', ((2,), 67.625, 6.625), (2, 68.375, 4.125),
          hw=0.125, layer_lock=[0, 0, 1])
add_items(journey_items_dense(J, 'CDR_LOL', hw=0.125))

others = [o for o in pool[2] if o[1] != 'I2C_SCL']
for (x, y) in ((68.2, 5.75), (69.0, 5.75), (69.8, 5.75), (70.4, 5.75),
               (71.1, 4.5), (71.1, 3.6), (71.1, 3.0), (70.9, 2.2),
               (70.0, 1.6), (69.35, 1.4), (68.6, 3.4), (67.5, 4.6),
               (67.5, 4.0)):
    m, b = L.pt_margin(2, x, y, 'I2C_SCL', 0.10, others)
    print(f'B ({x},{y}): track-pt margin {m:+.3f} binder {L.fmt_it(b)}',
          flush=True)
