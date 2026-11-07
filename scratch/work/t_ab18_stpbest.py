"""t_ab18: STP least-bad dive points with CK via placed at
(76.625,17.500) (its best stub-legal spot per t_ab17).
Prints the top margins over the whole south field (even when
negative) and names the binding item at the best point, per
layer - i.e. which fence would have to move, and by how much.
"""
import math, sys
sys.path.insert(0, 'hw')
import pcbnew
import repair, router
from router import netclass, dist_to_item

board = pcbnew.LoadBoard('scratch/work/t_ab17_base.kicad_pcb')
items, _ = repair.build_items(board)
CK = (76.625, 17.500, 0.30, 'ULPI_CK')
net = 'ULPI_STP'
R = 0.25

def margin_detail(x, y):
    worst = (9.9, None, None)
    for li in range(3):
        for it in items[li].near(li, x, y):
            if it[1] == net:
                continue
            need = R + max(netclass(net)[1],
                           netclass(it[1])[1] if it[1] else 0.2)
            m = dist_to_item(it, x, y) - need
            if m < worst[0]:
                worst = (m, li, it)
    ex, ey, er, en = CK
    need = R + er + max(netclass(net)[1], netclass(en)[1])
    m = math.hypot(x - ex, y - ey) - need
    if m < worst[0]:
        worst = (m, 'via', ('via', en, (ex, ey, er), 0.2))
    return worst

res = []
x0, x1, y0, y1 = 75.60, 77.40, 17.20, 18.60
nx = int(round((x1 - x0) / 0.125)) + 1
ny = int(round((y1 - y0) / 0.125)) + 1
for i in range(nx):
    for j in range(ny):
        x, y = x0 + i * 0.125, y0 + j * 0.125
        m, li, it = margin_detail(x, y)
        res.append((m, x, y, li, it))
res.sort(reverse=True)
for m, x, y, li, it in res[:10]:
    desc = ''
    if it:
        desc = (f'bind L{li} {it[0]} net={it[1]} '
                f'data={tuple(round(v, 3) for v in it[2])}')
    print(f'({x:.3f},{y:.3f}) margin {m:+.3f}  {desc}')
