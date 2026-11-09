import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
X0, X1, Y0, Y1 = 71.0, 75.5, 10.5, 17.5
for l in (2,):
    print(f'== layer {l}:', flush=True)
    for it in pool[l]:
        d = it[2]
        if it[0] == 'seg':
            x1, y1, x2, y2, hw = d
            if max(x1, x2) < X0 or min(x1, x2) > X1 \
                    or max(y1, y2) < Y0 or min(y1, y2) > Y1:
                continue
        elif not (X0 < d[0] < X1 and Y0 < d[1] < Y1):
            continue
        print('  ', L.fmt_it(it), flush=True)
print('PHY_1V8 fragments B chain check:', flush=True)
for net in ('PHY_1V8', 'DM_PHY', 'XO'):
    fs = fragsets(pool, net, (70.0, 80.0, 8.0, 21.0))
    print(net, 'fragments:', [len(f) for f in fs], flush=True)
