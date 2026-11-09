import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
# hypothetical GND via margins at candidate dive points
for (x, y) in ((69.6, 12.3), (69.3, 12.4), (68.9, 12.6), (69.6, 13.0),
               (70.3, 13.3), (68.5, 14.3), (69.05, 14.55)):
    via = ('via', 'GND', (x, y, 0.25), 0.2)
    ms = []
    for l in range(3):
        worst = 9.9
        for o in pool[l]:
            if o[1] == 'GND':
                continue
            worst = min(worst, item_margin(l, via, [o]))
        ms.append(worst)
    print(f'via ({x},{y}): F {ms[0]:+.3f} In2 {ms[1]:+.3f} B {ms[2]:+.3f}',
          flush=True)
astar = make_astar((67.0, 73.0, 10.5, 16.5), 0.05)
J = astar('GND', ((0,), 69.475, 12.75), (0, 71.8, 14.9), hw=0.10)
print('GND pad2(12.75) -> GND via (71.8,14.9):',
      'FOUND' if J else 'NONE', flush=True)
if J:
    print('  vias:', J['vias'], flush=True)
