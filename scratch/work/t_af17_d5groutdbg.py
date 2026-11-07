"""t_af17: debug the D4 In2 groute failure. Flood-fills
groute_in2's own passability grid from V4's seed and prints
an ASCII map of the corridor V4 -> A4 with the blocking
items named at the flood boundary.
"""
import math, sys
sys.path.insert(0, 'hw')

sys.argv = ['t_af11_d5d4small.py', 'hw/pdlvds_rx.exp216.kicad_pcb']
src = open('scratch/work/t_af11_d5d4small.py').read()
head = src.split('# ---- option build')[0]
g = {'__name__': 'af11model'}
exec(compile(head, 't_af11_head', 'exec'), g)

static_box = g['static_box']; TRK_HW = g['TRK_HW']
pt_margin = g['pt_margin']; pair_clr = g['pair_clr']
from router import dist_to_item

V4 = (79.96875, 14.53125); V5 = (80.25, 15.1875); V6 = (80.75, 14.625)
R = {'ULPI_D4': 0.25, 'ULPI_D5': 0.25, 'ULPI_D6': 0.30}
via5 = ('via', 'ULPI_D5', (V5[0], V5[1], R['ULPI_D5']), 0.2)
via6 = ('via', 'ULPI_D6', (V6[0], V6[1], R['ULPI_D6']), 0.2)
pool = static_box[1] + [via5, via6]
NET = 'ULPI_D4'

def worst_item(x, y):
    m, w = 9e9, None
    for it in pool:
        if it[1] == NET:
            continue
        d = dist_to_item(it, x, y) - TRK_HW - pair_clr(NET, it[1])
        if d < m:
            m, w = d, it
    return m, w

# ASCII map: x 79.0..81.5 step 0.125, y 13.0..15.5 step 0.125
print('map (rows = y descending; . passable, X blocked):')
for j in range(20, -1, -1):
    y = 13.0 + j * 0.125
    row = ''
    for i in range(21):
        x = 79.0 + i * 0.125
        m, _w = worst_item(x, y)
        row += '.' if m >= 0.004 else 'X'
    print(f'  y={y:6.3f} {row}')
print('   x: 79.0 ......... 80.0 ......... 81.0 ..... 81.5')
for label, P in (('V4', V4), ('A4', (80.625, 13.875)),
                 ('seed', (80.0, 14.5))):
    m, w = worst_item(P[0], P[1])
    print(f'{label} {P}: margin {m:+.3f} worst {w}')
# scan the straight corridor V4->A4
print('corridor samples V4->A4:')
for t in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
    x = V4[0] + (80.625 - V4[0]) * t
    y = V4[1] + (13.875 - V4[1]) * t
    m, w = worst_item(x, y)
    print(f'  t={t:.1f} ({x:.3f},{y:.3f}): {m:+.3f} worst {w}')
