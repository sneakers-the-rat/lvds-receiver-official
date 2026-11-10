"""t_bb2: XI fence census on exp254 + pocket-via grid optimisation.
Layers: 0=F, 1=In2, 2=B. Via candidate d0.5 (r0.25) through all layers.
Grid x[75.40,76.35] step 0.025, y[9.75,10.80]; margin = min over foreign
items on every layer (item_margin, model circles)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp254.kicad_pcb'
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)

print('--- fence census x[73.5,78.6] y[8.5,20.0] (nets of interest) ---')
NETS = ('ULPI_STP', 'PHY_1V8A', 'XO', 'ULPI_CK', '+3V3A', 'ULPI_DIR', 'XI')
for l in range(3):
    for it in pool[l]:
        if it[1] not in NETS:
            continue
        cc = C(it)
        if 73.5 <= cc[0] <= 78.6 and 8.5 <= cc[1] <= 20.0:
            d = it[2]
            if it[0] == 'seg':
                print(f'  {LAYN[l]:3} {it[1]:9} seg ({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f}) w{d[4] if len(d) > 4 else "?"}')
            elif it[0] == 'via':
                print(f'  {LAYN[l]:3} {it[1]:9} via ({d[0]:.2f},{d[1]:.2f}) r{d[2]:.2f}')
            else:
                print(f'  {LAYN[l]:3} {it[1]:9} {it[0]} ({d[0]:.2f},{d[1]:.2f})')

print('--- pocket grid (via d0.5, all layers) ---')
best = []
y = 9.75
while y <= 10.801:
    x = 75.40
    while x <= 76.351:
        cand = ('via', 'XI', (x, y, 0.25))
        worst = (9.9, None, None)
        for l in range(3):
            for o in pool[l]:
                if o[1] == 'XI':
                    continue
                oc = C(o)
                if abs(oc[0] - x) > 3.0 or abs(oc[1] - y) > 3.0:
                    continue
                m = item_margin(l, cand, [o])
                if m < worst[0]:
                    worst = (m, LAYN[l], o)
        best.append((round(worst[0], 3), round(x, 3), round(y, 3),
                     worst[1], worst[2][1] if worst[2] else None,
                     (round(C(worst[2])[0], 2), round(C(worst[2])[1], 2)) if worst[2] else None))
        x += 0.025
    y += 0.025
best.sort(reverse=True)
for row in best[:12]:
    print('  ', row)
