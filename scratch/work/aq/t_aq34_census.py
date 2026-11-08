import sys
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import load_items
board = pcbnew.LoadBoard(sys.argv[1])
items = load_items(board)
X0, X1, Y0, Y1 = (float(v) for v in sys.argv[2:6])
for li in range(3):
    print('--- layer', li)
    for kind, net, data, clr in items[li]:
        if kind == 'seg':
            x1, y1, x2, y2, hw = data
            if max(x1, x2) >= X0 and min(x1, x2) <= X1 and max(y1, y2) >= Y0 and min(y1, y2) <= Y1:
                print('  seg %-10s (%.3f,%.3f)->(%.3f,%.3f) hw%.3f' % (net, x1, y1, x2, y2, hw))
        elif kind == 'via':
            x, y, r = data
            if X0 - 0.5 <= x <= X1 + 0.5 and Y0 - 0.5 <= y <= Y1 + 0.5:
                print('  via %-10s (%.3f,%.3f) r%.3f' % (net, x, y, r))
        else:
            x, y, hwx, hwy, rot = data
            if X0 - 1 <= x <= X1 + 1 and Y0 - 1 <= y <= Y1 + 1:
                print('  pad %-10s (%.3f,%.3f) hw%.3fx%.3f' % (net, x, y, hwx, hwy))
