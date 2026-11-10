"""t_ba50: bisect the XI B-drop A* failure on the
excursion-free pool (exp253 + excursion ripped in model).
Goals south along the corridor; also dump XO F items in
x[71.5,76.6] y[9.2,10.2] (the west run's exact extent)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp253.kicad_pcb')
rip = []
for it in pool[2]:
    if it[1] != 'ULPI_STP' or it[0] != 'seg':
        continue
    cc = C(it)
    if 74.3 <= cc[0] <= 76.0 and 13.4 <= cc[1] <= 17.2:
        rip.append(it)
rip_items(rip)
print(f'excursion ripped {len(rip)}')

print('--- XO F x[71.5,76.6] y[9.2,10.2] (summary) ---')
xs, ys = [], []
for it in pool[0]:
    if it[1] != 'XO' or it[0] != 'seg':
        continue
    cc = C(it)
    if 71.5 <= cc[0] <= 76.6 and 9.2 <= cc[1] <= 10.2:
        xs.append(cc[0])
        ys.append(cc[1])
if xs:
    print(f'  {len(xs)} segs, centres x[{min(xs):.2f},{max(xs):.2f}] '
          f'y[{min(ys):.2f},{max(ys):.2f}]')

astar = make_astar((70.0, 80.0, 6.0, 22.0), 0.05)
for goal in [(75.6, 16.0), (75.6, 13.0), (75.4, 11.5), (75.2, 10.6),
             (75.05, 9.8)]:
    rr = astar('XI', ((2,), 75.625, 18.625), (2, goal[0], goal[1]), 0.10)
    print(f'goal {goal}:', 'FOUND' if rr else 'NONE')
print('=== done ===')
