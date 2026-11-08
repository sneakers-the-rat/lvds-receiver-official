import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, in_box_pool
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = load_items(board)
_tile = {}
def pool_for(l, x, y):
    key = (l, int(x // 2.0), int(y // 2.0))
    if key not in _tile:
        cx, cy = key[1] * 2.0, key[2] * 2.0
        sub = in_box_pool(items, (cx - 1.2, cx + 3.2, cy - 1.2, cy + 3.2))
        _tile[key] = sub[l]
    return _tile[key]
for (l, x, y) in [(2, 70.25, 10.0), (0, 76.0, 22.875), (1, 70.0, 10.0),
                  (2, 69.875, 3.125), (0, 70.625, 2.25), (2, 74.0, 20.0)]:
    p = pool_for(l, x, y)
    m, w = pt_margin(l, x, y, 'CAP_DATA', 0.1, p)
    print(f'L{l} ({x},{y}) pool {len(p)} margin {m:+.3f} worst {w}')
