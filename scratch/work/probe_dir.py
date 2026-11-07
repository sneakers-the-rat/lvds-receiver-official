import sys, math
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass
import router6
from router6 import seg_margin, via_margin, via_size, SAFE
b = pcbnew.LoadBoard('scratch/work/t_aa6.kicad_pcb')
items, pad_cells = repair.build_items(b)
for net, (vx, vy) in [('ULPI_DIR', (75.92, 17.42)), ('ULPI_NXT', (75.24, 17.15)),
                      ('ULPI_DIR', (69.28, -1.38)), ('ULPI_NXT', (69.30, -0.65))]:
    w, clr = netclass(net)
    vr = via_size(w)[0] / 2
    print(f"{net} via ({vx},{vy}) w={w} clr={clr} vr={vr} SAFE={SAFE} via_margin={via_margin(items, net, clr, vx, vy, vr):.3f}")
    for li, ln in [(0, 'F'), (2, 'In2'), (3, 'B')]:
        row = []
        for ang in range(0, 360, 45):
            dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            m = seg_margin(items, li, net, clr, vx, vy, vx + dx * 0.75, vy + dy * 0.75, w / 2)
            row.append(f"{ang}:{m:+.2f}")
        print(f"  {ln}: " + ' '.join(row))
