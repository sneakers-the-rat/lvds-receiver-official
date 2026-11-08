import sys, json, math
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import load_items, pt_margin, in_box_pool
BOARD, NET = sys.argv[1], sys.argv[2]
X0, X1, Y0, Y1 = (float(v) for v in sys.argv[3:7])
EXTRA = json.loads(sys.argv[7]) if len(sys.argv) > 7 else []
board = pcbnew.LoadBoard(BOARD)
items = load_items(board)
statics = {l: list(items[l]) for l in range(3)}
for e in EXTRA:
    if e[3] == e[5] and e[4] == e[6]:
        for li in range(3):
            statics[li].append(('via', e[0], (e[2], e[3], e[7] / 2), 0.2))
    else:
        statics[e[1]].append(('seg', e[0], (e[2], e[3], e[4], e[5], e[6] * 0.5), 0.2))
pools = in_box_pool(statics, (X0, X1, Y0, Y1), pad=0.7)
found = []
j = 0
while Y0 + j * 0.05 <= Y1 + 1e-9:
    y = Y0 + j * 0.05
    i = 0
    while X0 + i * 0.05 <= X1 + 1e-9:
        x = X0 + i * 0.05
        ms = [pt_margin(li, x, y, NET, 0.25, pools[li])[0] for li in range(3)]
        if min(ms) >= 0.0:
            found.append((x, y, min(ms)))
        i += 1
    j += 1
print('feasible via sites for %s: %d' % (NET, len(found)))
for x, y, m in found:
    print('  (%.2f,%.2f) worst %+.3f' % (x, y, m))
