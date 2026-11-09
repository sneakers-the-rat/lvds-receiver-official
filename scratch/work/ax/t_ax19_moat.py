import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool()
for net in ('THR_DAC', 'PG_3V3', 'ULPI_DIR', 'ULPI_NXT', 'I2C_SDA',
            'CAP_DATA'):
    print(f'== {net} B items in (66.5,71,-1,3.5):', flush=True)
    for it in pool[2]:
        if it[1] != net:
            continue
        d = it[2]
        if 66.5 < d[0] < 71.5 and -1.5 < d[1] < 4.0:
            print('  ', L.fmt_it(it), flush=True)
