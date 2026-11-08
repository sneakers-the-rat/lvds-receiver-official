"""t_aj5: probe passability along a point chain using groute's own
model (repair.build_items + router.dist_to_item + EPS_GRID 0.004).
Usage: t_aj5_probe2.py board NET LAYER(F|In2|B) RAD x,y;x,y;...
Prints per-point CLEAR/BLOCKED with the worst item."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

board = pcbnew.LoadBoard(sys.argv[1])
NET = sys.argv[2]
LI = {'F': 0, 'In2': 1, 'B': 2}[sys.argv[3]]
RAD = float(sys.argv[4])
items, _pc = repair.build_items(board)

def pair_clr(net, other):
    return max(netclass(net)[1], netclass(other)[1] if other else 0.2)

def probe(x, y):
    worst = (1e9, None)
    seen = set()
    for it in items[LI].near(LI, x, y):
        if it[1] == NET or id(it) in seen:
            continue
        seen.add(id(it))
        d = dist_to_item(it, x, y) - RAD - pair_clr(NET, it[1])
        if d < worst[0]:
            worst = (d, it)
    return worst

for spec in sys.argv[5].split(';'):
    x, y = map(float, spec.split(','))
    d, it = probe(x, y)
    tag = 'CLEAR' if d >= 0.004 else 'BLOCKED'
    desc = ''
    if it is not None:
        desc = f'{it[0]} {it[1]} {tuple(round(v,3) for v in it[2])}'
    print(f'{tag} ({x},{y}) margin {d:+.3f} vs {desc}')
