"""t_aj3: margin breakdown at a point for NET, per layer, worst-first.
Usage: t_aj3_probe.py board NET X Y RAD"""
import sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
import t_ai_lib as L
from router import dist_to_item

board = pcbnew.LoadBoard(sys.argv[1])
NET = sys.argv[2]
X, Y, RAD = map(float, sys.argv[3:6])
items = L.load_items(board)
for li, ln in enumerate(['F', 'In2', 'B']):
    rows = []
    for it in items[li]:
        if it[1] == NET:
            continue
        d = dist_to_item(it, X, Y) - RAD - L.pair_clr(NET, it[1])
        rows.append((d, it))
    rows.sort(key=lambda t: t[0])
    print(f'--- layer {ln}: worst margins at ({X},{Y}) rad {RAD}')
    for d, it in rows[:5]:
        print(f'    {d:+.3f}  {L.fmt_it(it)}')
