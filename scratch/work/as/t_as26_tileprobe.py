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
for (x, y) in [(69.875, 4.5), (69.875, 4.5625), (69.875, 4.625),
               (69.875, 4.75), (69.75, 4.875)]:
    p = pool_for(0, x, y)
    m, w = pt_margin(0, x, y, 'CAP_DATA', 0.1, p)
    print(f'F ({x},{y}) tilepool {len(p)} margin {m:+.3f} worst {w}')
