"""t_ax25: door-1 + eastern B descent test.
Fresh pool; move SCL via (69.625,12.625)->(69.5,12.75); shrink
+3V3D via (70.875,12.625) r0.4->r0.25; then A* SCL B-locked
(69.5,12.75)->(69.35,1.4) hw0.10 box (68.5,74.5,0,13.5);
fallback ML. Gate the journey if found."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

pool = load_board_pool()
old = ('via', 'I2C_SCL', (69.625, 12.625, 0.3), 0.2)
# find actual via item (radius may differ)
cands = [it for it in pool[0] if it[0] == 'via' and it[1] == 'I2C_SCL'
         and abs(it[2][0] - 69.625) < 0.01 and abs(it[2][1] - 12.625) < 0.01]
print('stub via items:', [L.fmt_it(c) for c in cands], flush=True)
for c in cands:
    rip_items([c])
newvia = ('via', 'I2C_SCL', (69.5, 12.75, cands[0][2][2]), 0.2)
add_items({0: [newvia], 2: [newvia]})
pool[1].append(newvia)
c3 = [it for it in pool[0] if it[0] == 'via' and it[1] == '+3V3D'
      and abs(it[2][0] - 70.875) < 0.01 and abs(it[2][1] - 12.625) < 0.01]
print('+3V3D via items:', [L.fmt_it(c) for c in c3], flush=True)
for c in c3:
    rip_items([c])
nv3 = ('via', '+3V3D', (70.875, 12.625, 0.25), 0.25)
add_items({0: [nv3], 2: [nv3]})
pool[1].append(nv3)

for lock, nm in (([0, 0, 1], 'B-locked'), (None, 'ML')):
    astar = make_astar((68.5, 74.5, 0.0, 13.5), 0.025)
    J = astar('I2C_SCL', ((2,), 69.5, 12.75), (2, 69.35, 1.4), hw=0.10,
              layer_lock=lock)
    print(f'A* {nm}:', 'FOUND' if J else 'NONE', flush=True)
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
