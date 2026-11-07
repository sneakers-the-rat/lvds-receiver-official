"""t_ac4: who blocks a point? For each probe point and layer, list
every foreign item whose edge distance is within (rad + pair_clr
+ slack), sorted nearest first — i.e. the items that make the cell
impassable for a track (rad 0.1) or a via (rad 0.25).

Usage: xvfb-run -a python3 scratch/work/t_ac4_blockers.py BOARD NET \
       x,y[,rad] [x,y[,rad] ...]
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

src, net = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
items, _pc = repair.build_items(board)
LAYN = ['F', 'In2', 'B']

def pair_clr(other):
    return max(netclass(net)[1], netclass(other)[1] if other else 0.2)

for spec in sys.argv[3:]:
    parts = spec.split(',')
    x, y = float(parts[0]), float(parts[1])
    rad = float(parts[2]) if len(parts) > 2 else 0.1
    print(f'=== probe ({x:.3f},{y:.3f}) rad {rad} ===')
    for li in range(3):
        rows = []
        seen = set()
        for it in items[li].near(li, x, y):
            if it[1] == net or id(it) in seen:
                continue
            seen.add(id(it))
            d = dist_to_item(it, x, y)
            need = rad + pair_clr(it[1])
            if d < need + 0.35:
                rows.append((d - need, d, it))
        rows.sort()
        for marg, d, it in rows:
            kind, onet, geo = it[0], it[1], it[2]
            print(f'  {LAYN[li]} margin {marg:+.3f} dist {d:.3f} '
                  f'{kind} [{onet}] {geo}')
