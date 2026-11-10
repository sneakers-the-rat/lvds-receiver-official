"""t_bb28: identify the under-chip B corridor contents on exp256:
all B items with centre x[74.0,78.0] y[12.0,16.2]; all vias inside
the U7 EP rect x[74.45,77.55] y[12.45,15.55] (any net); STP B chain
south of y13 (full net path through the corridor)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp256.kicad_pcb')
print('--- B items centre x[74.0,78.0] y[12.0,16.2] ---')
rows = []
for it in pool[2]:
    c = C(it)
    if 74.0 <= c[0] <= 78.0 and 12.0 <= c[1] <= 16.2:
        rows.append((round(c[1], 2), round(c[0], 2), it))
for _, _, it in sorted(rows):
    print('  B  ', it[1].ljust(10), L.fmt_it(it))
print(f'  ({len(rows)} items)')
print('--- vias inside EP rect (any layer list, B list) ---')
for it in pool[2]:
    if it[0] == 'via':
        x, y = it[2][0], it[2][1]
        if 74.45 <= x <= 77.55 and 12.45 <= y <= 15.55:
            print('  via', it[1].ljust(10), L.fmt_it(it))
print('--- ULPI_STP B items y[12.9,18.2] x[75.8,76.8] (chain + dive) ---')
for it in pool[2]:
    if it[1] != 'ULPI_STP':
        continue
    c = C(it)
    if 75.8 <= c[0] <= 76.8 and 12.9 <= c[1] <= 18.2:
        print('  B   ULPI_STP', L.fmt_it(it))
