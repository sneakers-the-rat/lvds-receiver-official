"""t_ba34: +3V3A In2 items x[74.5,77.5] y[7.5,11.5] exact;
then a fine grid for STP's transition via V in
x[76.15,77.05] y[8.85,9.65] (0.05): gate V + B-descent
extension (76.2,10.5)->V + In2 seg V->(77.2,5.9) against
the full pool (STP south ripped). Report the feasible
set's extent + best points."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp252.kicad_pcb')
print('--- +3V3A In2 x[74.5,77.5] y[7.5,11.5] ---')
for it in pool[1]:
    if it[1] != '+3V3A':
        continue
    cc = C(it)
    if 74.5 <= cc[0] <= 77.5 and 7.5 <= cc[1] <= 11.5:
        d = it[2]
        if it[0] == 'seg':
            print(f'  seg ({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},'
                  f'{d[3]:.2f}) hw{d[4]}')
        elif it[0] == 'via':
            print(f'  via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}')
        else:
            print(f'  pad ({d[0]:.2f},{d[1]:.2f})')

rip = []
for l in range(3):
    for it in pool[l]:
        if it[1] != 'ULPI_STP' or it[0] not in ('seg', 'via'):
            continue
        cc = C(it)
        if 75.5 <= cc[0] <= 78.5 and 7.0 <= cc[1] <= 14.0:
            rip.append(it)
        elif 0.5 < cc[1] < 7.5 and cc[0] > 72.0:
            rip.append(it)
rip_items(rip)


def worst(items_by_layer):
    w, wo = 9.9, None
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                cc, ci = C(o), C(it)
                if abs(cc[0] - ci[0]) > 3.5 or abs(cc[1] - ci[1]) > 3.5:
                    continue
                m = item_margin(l, it, [o])
                if m < w:
                    w, wo = m, (l, o[1])
    return w, wo


feas = []
for i in range(19):
    for j in range(17):
        vx, vy = 76.15 + i * 0.05, 8.85 + j * 0.05
        items = {2: [('seg', 'ULPI_STP', (76.2, 10.5, vx, vy, 0.10), 0.2)],
                 1: [('seg', 'ULPI_STP', (vx, vy, 77.2, 5.9, 0.10), 0.2)]}
        for l in range(3):
            items.setdefault(l, []).append(
                ('via', 'ULPI_STP', (vx, vy, 0.25), 0.2))
        w, wo = worst(items)
        feas.append((round(w, 3), (round(vx, 2), round(vy, 2)), wo))
feas.sort(reverse=True)
print('best transition-via candidates:')
for f in feas[:8]:
    print('  ', f)
ok = [f for f in feas if f[0] >= 0]
print(f'feasible: {len(ok)}')
if ok:
    xs = [f[1][0] for f in ok]
    ys = [f[1][1] for f in ok]
    print(f'  x range {min(xs)}..{max(xs)}, y range {min(ys)}..{max(ys)}')
print('=== done ===')
