import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp248.kicad_pcb')
for net in ('REFCLKN', 'REFCLK'):
    print(f'== {net} items in (63,80,30,41):', flush=True)
    seen = set()
    for lay in range(3):
        for it in pool[lay]:
            if it[1] != net:
                continue
            d = it[2]
            if 63 < d[0] < 80 and 30 < d[1] < 41:
                s = 'L%d ' % lay + L.fmt_it(it)
                if s not in seen:
                    seen.add(s)
                    print('  ', s, flush=True)
print('== GND items in (71,74.5,35,38.5):', flush=True)
seen = set()
for lay in range(3):
    for it in pool[lay]:
        if it[1] != 'GND':
            continue
        d = it[2]
        if 71 < d[0] < 74.5 and 35 < d[1] < 38.5:
            s = 'L%d ' % lay + L.fmt_it(it)
            if s not in seen:
                seen.add(s)
                print('  ', s, flush=True)
