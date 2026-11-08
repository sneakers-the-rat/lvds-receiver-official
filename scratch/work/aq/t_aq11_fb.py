"""t_aq11: F and B census box x[69,78] y[2,11] on exp235."""
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


for li, nm in ((0, 'F'), (2, 'B')):
    print(f'=== {nm} items, centre in x[69,78] y[2,11] ===')
    for it in items[li]:
        x, y = centre(it)
        if 69 <= x <= 78 and 2 <= y <= 11:
            print(fmt_it(it))
