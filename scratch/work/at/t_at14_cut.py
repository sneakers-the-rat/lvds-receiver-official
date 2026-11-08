"""t_at14: netclass values + perpendicular field cut across the
band channel at x+y const lines; samples along the direction NE of
the band through point (67.5,2.0), listing top-3 binding items."""
import wx
_app = wx.App(False)
import pcbnew, sys, math
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass
for n in ('CAP_CLK', 'CAP_DATA', 'HV_SHDN', 'I2C_SCL', 'I2C_SDA',
          'THR_DAC', 'PG_3V3', 'ULPI_NXT', 'ULPI_DIR', '+3V3D', 'XO',
          '+3V3A', 'GND'):
    print(n, netclass(n))
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)
BOX = (63.0, 73.0, -1.0, 8.0)
pool = L.in_box_pool(items, BOX, pad=0.6)
# cut: start on band line at (67.5,2.0) (x+y=69.5), step NE (1,1)/sqrt2
import numpy as np
for t in np.arange(0.0, 2.21, 0.1):
    x = 67.5 + t / math.sqrt(2)
    y = 2.0 + t / math.sqrt(2)
    rows = []
    for it in pool[1]:
        if it[1] in ('CAP_CLK', 'CAP_DATA'):
            continue
        d = L.dist_to_item(it, x, y)
        req = max(netclass('CAP_CLK')[1], it[3])
        rows.append((d - req, it))
    rows.sort(key=lambda r: r[0])
    top = ' | '.join(f'{v:+.3f} {L.fmt_it(it)}' for v, it in rows[:3])
    print(f't={t:.1f} ({x:.2f},{y:.2f}): {top}')
