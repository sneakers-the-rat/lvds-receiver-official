import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
# reproduce v4 edits up to the +3V3A rip
c23 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 14.75) < 0.01 and it[2][0] in (69.975, 71.525)]
gndvia = [it for it in pool[0] if it[0] == 'via' and it[1] == 'GND'
          and abs(it[2][0] - 71.8) < 0.01 and abs(it[2][1] - 14.9) < 0.01]
rip_items(c23 + gndvia)
add_items({0: [('pad', 'GND', (69.975, 14.75, 0.450, 0.475, 0.0), 0.2),
               ('pad', 'PHY_1V8A', (71.525, 14.75, 0.450, 0.475, 0.0), 0.2)]})
goal = {0: [('seg', 'PHY_1V8A', (72.3, 14.45, 72.0, 14.55, 0.10), 0.2),
            ('seg', 'PHY_1V8A', (72.0, 14.55, 71.9, 14.6, 0.10), 0.2)],
        1: [], 2: []}
for l in range(3):
    goal[l].append(('via', 'PHY_1V8A', (72.3, 14.45, 0.25), 0.2))
add_items(goal)
diag = [it for it in pool[0] if it[1] == '+3V3A' and it[0] == 'seg'
        and abs(it[2][0] - 72.625) < 0.01 and abs(it[2][1] - 14.625) < 0.01]
print('diag segs:', [L.fmt_it(i) for i in diag], flush=True)
rip_items(diag)
for label, goalp in (('(72.9,14.3)', (0, 72.9, 14.3)),
                     ('(73.3,14.7)', (0, 73.3, 14.7)),
                     ('(73.562,14.75) pad', (0, 73.562, 14.75))):
    astar = make_astar((71.0, 75.0, 12.5, 16.0), 0.05)
    J = astar('+3V3A', ((0,), 72.25, 13.875), goalp, hw=0.10)
    print(f'+3V3A -> {label}:', 'FOUND' if J else 'NONE', flush=True)
# F items near the corridor (72,74,13.5,15.5)
print('== F items (72,74.5,13.5,15.6):', flush=True)
seen = set()
for it in pool[0]:
    d = it[2]
    if 72 < d[0] < 74.5 and 13.5 < d[1] < 15.6:
        s = L.fmt_it(it)
        if s not in seen:
            seen.add(s)
            print('  ', s, flush=True)
