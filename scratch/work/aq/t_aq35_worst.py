import sys, json
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import load_items, pt_margin, in_box_pool
board = pcbnew.LoadBoard(sys.argv[1])
NET = sys.argv[2]
items = load_items(board)
statics = {l: list(items[l]) for l in range(3)}
for (x, y) in [(float(a), float(b)) for a, b in zip(sys.argv[3::2], sys.argv[4::2])]:
    for li in range(3):
        box = (x - 1.2, x + 1.2, y - 1.2, y + 1.2)
        pool = in_box_pool(statics, box, pad=0.7)[li]
        m, w = pt_margin(li, x, y, NET, 0.1, pool)
        print('(%s,%s) L%d margin %+.3f worst %s' % (x, y, li, m, w))
