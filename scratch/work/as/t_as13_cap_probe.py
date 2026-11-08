"""t_as13: worst-fence probe for sealed CAP endpoints on exp240."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, in_box_pool

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp240.kicad_pcb')
items = load_items(board)

PROBES = [
    ('CAP_CLK', [(75.2, 25.385), (74.8, 25.385), (75.2, 25.9), (74.5, 25.9),
                 (75.0, 24.7), (74.6, 24.6), (75.4, 26.1)]),
    ('CAP_DATA', [(70.45, 2.25), (70.2, 2.5), (69.9, 2.25), (70.5, 2.7),
                  (70.45, 1.75), (70.2, 1.5), (69.9, 1.75), (70.5, 1.3),
                  (70.9, 2.9), (70.9, 1.2)]),
    ('CAP_CLK', [(70.45, 1.75), (70.2, 1.5), (69.9, 1.75), (70.5, 1.3),
                 (70.9, 1.2), (70.9, 2.9)]),
]
for net, pts in PROBES:
    for (x, y) in pts:
        worst = (9, None, None)
        for l in range(3):
            m, w = pt_margin(l, x, y, net, 0.25, items[l])
            if m < worst[0]:
                worst = (m, l, w)
        print(f'{net} via ({x},{y}): worst {worst[0]:+.3f} L{worst[1]} {worst[2]}')
    print()
