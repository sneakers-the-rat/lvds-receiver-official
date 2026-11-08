"""t_aq10: full In2 census box x[67,77] y[2,14] on exp235 + BIST chain."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp235.kicad_pcb')
items = load_items(b)


def centre(it):
    k, d = it[0], it[2]
    if k in ('pad', 'via'):
        return d[0], d[1]
    return (d[0] + d[2]) / 2, (d[1] + d[3]) / 2


print('=== In2 items, centre in x[67,77] y[2,14] ===')
for it in items[1]:
    x, y = centre(it)
    if 67 <= x <= 77 and 2 <= y <= 14:
        print(fmt_it(it))
print('=== BIST_DRV all layers, full chain ===')
for li in range(3):
    for it in items[li]:
        if it[1] == 'BIST_DRV':
            print(f'L{li} {fmt_it(it)}')
