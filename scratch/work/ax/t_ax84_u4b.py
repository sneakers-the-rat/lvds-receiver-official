import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp248.kicad_pcb')
for lay, nm in ((1, 'In2'), (2, 'B')):
    print(f'== {nm} items in (66,74,33,40):', flush=True)
    seen = set()
    for it in pool[lay]:
        d = it[2]
        if 66 < d[0] < 74 and 33 < d[1] < 40:
            s = L.fmt_it(it)
            if s not in seen:
                seen.add(s)
                print('  ', s, flush=True)
print('== F items touching I2C_SDA / I2C_SCL near U4:', flush=True)
for lay, nm in ((0, 'F'), (1, 'In2'), (2, 'B')):
    for it in pool[lay]:
        if it[1] in ('I2C_SDA', 'I2C_SCL'):
            d = it[2]
            if d[0] > 66 and d[1] > 30:
                print(f'  {nm}', L.fmt_it(it), flush=True)
