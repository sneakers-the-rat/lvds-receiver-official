import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
print('== +3V3D F items with any endpoint in (73.5,76,7,10.5):', flush=True)
for it in pool[0]:
    if it[1] != '+3V3D':
        continue
    d = it[2]
    pts = [(d[0], d[1])] + ([(d[2], d[3])] if it[0] == 'seg' else [])
    if any(73.5 < p[0] < 76.0 and 7.0 < p[1] < 10.5 for p in pts):
        print('  ', L.fmt_it(it), flush=True)
print('== XO In2 items touching (72.625,12.25):', flush=True)
n = 0
for it in pool[1]:
    if it[1] != 'XO':
        continue
    d = it[2]
    pts = [(d[0], d[1])] + ([(d[2], d[3])] if it[0] == 'seg' else [])
    if any(abs(p[0] - 72.625) < 0.01 and abs(p[1] - 12.25) < 0.01
           for p in pts):
        print('  ', L.fmt_it(it), flush=True)
        n += 1
print('   count:', n, flush=True)
