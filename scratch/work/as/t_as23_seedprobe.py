import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, in_box_pool
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = load_items(board)
pool = in_box_pool(items, (66.5, 73.0, 0.5, 6.5))
for (x, y) in [(69.875, 3.125), (69.875, 3.25), (69.75, 3.125), (70.0, 3.125),
               (69.875, 3.0), (69.75, 3.25), (70.0, 3.25), (69.75, 3.0),
               (70.0, 3.0)]:
    row = []
    for l in range(3):
        m, w = pt_margin(l, x, y, 'CAP_DATA', 0.1, pool[l])
        row.append(f'L{l} {m:+.3f} {w[1] if w else ""}')
    print((x, y), ' | '.join(row))
