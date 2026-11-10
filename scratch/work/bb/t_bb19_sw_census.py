"""t_bb19: full B census x[66,77] y[16,24] on exp254 + journey ends
for DP_PHY, CAP_DATA, ULPI_DIR on B."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp254.kicad_pcb')
rows = []
for it in pool[2]:
    c = C(it)
    if 66.0 <= c[0] <= 77.0 and 16.0 <= c[1] <= 24.0:
        rows.append((round(c[1], 2), round(c[0], 2), it))
print(f'B items in box: {len(rows)}')
for _, _, it in sorted(rows):
    print('  B  ', it[1].ljust(10), L.fmt_it(it))
