"""t_at18: probe top-6 nearest L1 items at bind cells in v6 pool."""
import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

src = open('scratch/work/at/t_at16_astar6.py').read()
exec(src.split('X0, X1, Y0, Y1, ST')[0].split('def gate_news')[0])

for (x, y) in ((67.6, 2.4), (66.6, 3.4), (68.7, 1.3), (65.6, 4.4)):
    rows = []
    for it in pool[1]:
        if it[1] in ('CAP_CLK',):
            continue
        d = L.dist_to_item(it, x, y)
        req = max(netclass('CAP_CLK')[1], it[3])
        rows.append((d - req, it))
    rows.sort(key=lambda r: r[0])
    print(f'-- ({x},{y}):')
    for v, it in rows[:6]:
        print(f'   {v:+.3f} {L.fmt_it(it)}')
