import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
X0, X1, Y0, Y1 = 69.5, 74.5, 16.0, 21.5
for l in (2, 1):
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
