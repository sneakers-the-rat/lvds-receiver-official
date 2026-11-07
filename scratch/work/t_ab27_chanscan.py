"""t_ab27: legal via points in the DM<->REFCLK channel on
exp213, for ULPI_DIR and ULPI_NXT (d0.5), exact item geometry.
Prints every on-grid point with margin >= 0 per net, so a
compatible pair (centres >= 0.70 apart) can be picked.
"""
import math, sys
sys.path.insert(0, 'hw')
import pcbnew
import repair, router
from router import netclass, dist_to_item

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp213.kicad_pcb')
items, _ = repair.build_items(board)

def via_margin(x, y, r, net):
    worst = 9.9
    for li in range(3):
        for it in items[li].near(li, x, y):
            if it[1] == net:
                continue
            need = r + max(netclass(net)[1],
                           netclass(it[1])[1] if it[1] else 0.2)
            worst = min(worst, dist_to_item(it, x, y) - need)
    return worst

for net in ('ULPI_DIR', 'ULPI_NXT'):
    pts = []
    x0, x1, y0, y1 = 65.75, 68.75, 27.50, 32.75
    nx = int(round((x1 - x0) / 0.125)) + 1
    ny = int(round((y1 - y0) / 0.125)) + 1
    for i in range(nx):
        for j in range(ny):
            x, y = x0 + i * 0.125, y0 + j * 0.125
            m = via_margin(x, y, 0.25, net)
            if m >= 0:
                pts.append((round(m, 3), x, y))
    pts.sort(reverse=True)
    print(f'{net}: {len(pts)} legal via points in channel box')
    for m, x, y in pts:
        print(f'   ({x:.3f},{y:.3f}) +{m:.3f}')
