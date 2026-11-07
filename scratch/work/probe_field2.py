import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass
from router6 import via_margin, via_size
b = pcbnew.LoadBoard('scratch/work/t_aa6.kicad_pcb')
items, pad_cells = repair.build_items(b)
for net in ['ULPI_DIR', 'ULPI_NXT', 'ULPI_STP']:
    w, clr = netclass(net)
    vr = via_size(w)[0] / 2
    pts = []
    y = 16.90
    while y <= 18.45:
        x = 75.90 if net != 'ULPI_NXT' else 74.95
        while x <= 78.60:
            vm = via_margin(items, net, clr, x, y, vr)
            if vm >= 0.0:
                pts.append((round(vm, 3), round(x, 2), round(y, 2)))
            x += 0.05
        y += 0.05
    pts.sort(reverse=True)
    print(f"== {net}: {len(pts)} via-legal points; best:")
    for p in pts[:20]: print("   vm=%.3f at (%.2f, %.2f)" % p)
