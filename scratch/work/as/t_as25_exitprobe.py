import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, in_box_pool
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = load_items(board)
pool = in_box_pool(items, (67.5, 72.5, 3.0, 7.0))
PTS = [(69.875, 4.625), (69.75, 4.875), (70.0, 4.75), (69.875, 4.75),
       (69.625, 4.875), (70.125, 4.625), (69.5, 5.125), (69.25, 4.375),
       (69.25, 4.125), (70.25, 4.875), (69.125, 5.0), (68.9, 4.5)]
for net in ('CAP_DATA', 'CAP_CLK'):
    print(f'--- {net} (track rad 0.1) ---')
    for (x, y) in PTS:
        out = []
        for l in range(3):
            m, w = pt_margin(l, x, y, net, 0.1, pool[l])
            out.append(f'L{l} {m:+.3f} {w[1] if w else ""}')
        print((x, y), ' | '.join(out))
