"""t_ab5: name the blockers around a point/region for a net.

Usage: t_ab5_dbg.py BOARD NET X Y [RAD]
Prints every foreign item within RAD mm of (X,Y) per layer with
its edge distance, and the demand rad+clr+eps for track/via.
"""
import math, sys
sys.path.insert(0, 'hw')
import pcbnew
import repair, router
from router import netclass, dist_to_item

net = sys.argv[2]
X, Y = float(sys.argv[3]), float(sys.argv[4])
RAD = float(sys.argv[5]) if len(sys.argv) > 5 else 0.1
board = pcbnew.LoadBoard(sys.argv[1])
items, _ = repair.build_items(board)
for li, ln in enumerate(('F', 'In2', 'B')):
    print(f'--- layer {ln} around ({X},{Y}) net {net}')
    found = []
    for it in items[li].near(li, X, Y):
        if it[1] == net:
            continue
        d = dist_to_item(it, X, Y)
        clr = max(netclass(net)[1], netclass(it[1])[1] if it[1] else 0.2)
        if d < RAD + clr + 0.6:
            found.append((d, it, clr))
    for d, it, clr in sorted(found):
        print(f'  d={d:6.3f} need_trk={0.1 + clr:.3f} need_via={0.25 + clr:.3f} '
              f'{it[0]} net={it[1]!r} data={tuple(round(v, 3) for v in it[2])}')
