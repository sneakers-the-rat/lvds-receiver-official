import sys, json
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import load_items, pt_margin, in_box_pool

BOARD, NET = sys.argv[1], sys.argv[2]
X0, X1, Y0, Y1 = (float(v) for v in sys.argv[3:7])
LI = int(sys.argv[7]) if len(sys.argv) > 7 else 1
EXTRA = json.loads(sys.argv[8]) if len(sys.argv) > 8 else []
board = pcbnew.LoadBoard(BOARD)
items = load_items(board)
statics = {l: list(items[l]) for l in range(3)}
for e in EXTRA:
    statics[e[1]].append(('seg', e[0], (e[2], e[3], e[4], e[5], e[6] * 0.5), 0.2))
pool = in_box_pool(statics, (X0, X1, Y0, Y1), pad=0.7)[LI]
step = 0.25
ny = int((Y1 - Y0) / step) + 1
nx = int((X1 - X0) / step) + 1
print('L%d margin map, net %s (free=. knife=o blocked=#)' % (LI, NET))
for j in range(ny - 1, -1, -1):
    y = Y0 + j * step
    row = ''
    for i in range(nx):
        x = X0 + i * step
        m = pt_margin(LI, x, y, NET, 0.1, pool)[0]
        row += '.' if m >= 0.05 else ('o' if m >= -0.001 else '#')
    print('%6.2f %s' % (y, row))
print('       ' + ''.join(str(int((X0 + i * step) // 10 % 10)) for i in range(nx)))
print('       ' + ''.join(str(int((X0 + i * step) % 10)) for i in range(nx)))
