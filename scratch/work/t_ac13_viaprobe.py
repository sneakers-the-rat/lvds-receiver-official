"""t_ac13: via_ok / trk_ok probe at arbitrary points under the
t_ab2 DRC-rule model (same geometry code as t_ac2).

Usage: xvfb-run -a python3 scratch/work/t_ac13_viaprobe.py BOARD NET x,y [x,y ...]
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

src, net = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
items, _pc = repair.build_items(board)

def pair_clr(other):
    return max(netclass(net)[1], netclass(other)[1] if other else 0.2)

def pt_clear(li, x, y, rad, eps=0.004):
    seen = set()
    for it in items[li].near(li, x, y):
        if it[1] == net or id(it) in seen:
            continue
        seen.add(id(it))
        if dist_to_item(it, x, y) < rad + pair_clr(it[1]) + eps:
            return False
    return True

for spec in sys.argv[3:]:
    x, y = map(float, spec.split(','))
    trk = [pt_clear(li, x, y, 0.1) for li in range(3)]
    via = all(pt_clear(li, x, y, 0.25) for li in range(3))
    print(f'({x:.3f},{y:.3f}) trk F/In2/B={trk} via_ok={via}')
