import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
X0, X1, Y0, Y1 = 66.5, 72.5, 15.5, 19.5
for l in (1,):
    print(f'== layer {l}:', flush=True)
    seen = set()
    for it in pool[l]:
        d = it[2]
        if it[0] == 'seg':
            x1, y1, x2, y2, hw = d
            if max(x1, x2) < X0 or min(x1, x2) > X1 \
                    or max(y1, y2) < Y0 or min(y1, y2) > Y1:
                continue
        elif not (X0 < d[0] < X1 and Y0 < d[1] < Y1):
            continue
        s = L.fmt_it(it)
        if s not in seen:
            seen.add(s)
            print('  ', s, flush=True)
# dive-only test on modified pool
c20 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.5) < 0.01 and it[2][0] in (75.725, 77.275)]
rip_items(c20)
arm = []
for it in pool[2]:
    if it[1] == 'PHY_1V8' and it[0] == 'seg' and it[2][1] >= 16.0 \
            and max(it[2][0], it[2][2]) <= 77.85:
        arm.append(it)
arm += [it for it in pool[2] if it[0] == 'via'
        and ((abs(it[2][0] - 71.375) < 0.01 and abs(it[2][1] - 17.625) < 0.01)
             or (abs(it[2][0] - 73.434) < 0.01
                 and abs(it[2][1] - 17.685) < 0.01))]
rip_items(arm)
box = (66.0, 78.5, -4.0, 19.5)
for label, g in (('I (71.5,17.4) dive-only', (1, 71.5, 17.4)),
                 ('I (70.0,17.8)', (1, 70.0, 17.8)),
                 ('I (68.6,17.8)', (1, 68.6, 17.8))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', ((2,), 71.5, 17.4), g, hw=0.10)
    print(f'{label}:', 'FOUND vias=' + str(J['vias']) if J else 'NONE',
          flush=True)
