"""t_at8: attribute the clearance field at given points (layer, x, y)
against exp241esc items (minus band7) + jogged band + S via."""
import wx
_app = wx.App(False)
import pcbnew, sys, math
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import dist_to_item, netclass

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)
pts = [(1, 68.55, 1.45), (1, 68.50, 1.50), (1, 68.60, 1.40),
       (1, 68.85, 1.15), (0, 74.65, 25.05)]
for li, x, y in pts:
    rows = []
    for it in items[li]:
        if it[1] in ('CAP_CLK', 'CAP_DATA'):
            continue
        dd = dist_to_item(it, x, y) - max(0.2, it[3])
        rows.append((dd, it))
    rows.sort(key=lambda r: r[0])
    print(f'-- L{li} ({x},{y}):')
    for dd, it in rows[:4]:
        print(f'   {dd:+.3f}  {L.fmt_it(it)}')
