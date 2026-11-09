"""t_ax3: baseline on the SHIPPED exp241 pool.
1) ML A* SCL frag0 anchors -> pocket targets (expect NONE, matching aw).
2) Viafit scan: SCL via r0.25 legal points over (63.5,71.5,-1,9.5)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

pool = load_board_pool()

astar = make_astar((62.0, 72.0, -2.0, 14.0), 0.025)
starts = [((0, 1, 2), 66.875, 6.75), ((0, 1, 2), 69.625, 12.625)]
goals = [(0, 69.35, 1.4), (1, 69.35, 1.4), (2, 69.35, 1.4),
         (0, 66.15, 2.1), (0, 66.5, 1.63)]
for s in starts:
    for gl in goals:
        J = astar('I2C_SCL', s, gl, hw=0.10)
        print(f'A* {s[1]},{s[2]} -> L{gl[0]} ({gl[1]},{gl[2]}): '
              f'{"FOUND" if J else "NONE"}', flush=True)

print('--- viafit scan (SCL via r0.25) ---', flush=True)
others = {l: [it for it in pool[l] if it[1] != 'I2C_SCL'] for l in range(3)}
legal = []
y = -1.0
while y <= 9.5:
    x = 63.5
    row = []
    while x <= 71.5:
        m = min(L.pt_margin(l, x, y, 'I2C_SCL', 0.25, others[l])[0]
                for l in range(3))
        if m >= 0:
            legal.append((round(x, 2), round(y, 2), round(m, 3)))
            row.append('#')
        elif m >= -0.1:
            row.append('+')
        else:
            row.append('.')
        x += 0.25
    print(f'y={y:5.2f} ' + ''.join(row), flush=True)
    y += 0.25
print(f'legal via points: {len(legal)}', flush=True)
for p in legal:
    print('  ', p, flush=True)
