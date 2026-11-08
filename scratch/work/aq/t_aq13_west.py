"""t_aq13: full census x[58,72] y[0,16], all layers, exp235.
Endpoint-based inclusion (a seg counts if either endpoint is in
the box) so nothing straddling the edge is dropped."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp235.kicad_pcb')
items = load_items(b)
X0, X1, Y0, Y1 = 58, 72, 0, 16
for li, nm in ((0, 'F'), (1, 'In2'), (2, 'B')):
    print(f'=== {nm} ===')
    for it in items[li]:
        d = it[2]
        if it[0] == 'seg':
            if (X0 <= d[0] <= X1 and Y0 <= d[1] <= Y1) or \
               (X0 <= d[2] <= X1 and Y0 <= d[3] <= Y1):
                print(fmt_it(it))
        else:
            if X0 <= d[0] <= X1 and Y0 <= d[1] <= Y1:
                print(fmt_it(it))
