import sys, math
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass
from router6 import seg_margin, via_margin, via_size
b = pcbnew.LoadBoard('scratch/work/t_aa6.kicad_pcb')
items, pad_cells = repair.build_items(b)
F = 0
for net, pad in [('ULPI_NXT', (75.25, 16.438)), ('ULPI_DIR', (75.75, 16.438))]:
    w, clr = netclass(net)
    vr = via_size(w)[0] / 2
    print(f"== {net} w={w} clr={clr} vr={vr}")
    best = []
    y = 16.95
    while y <= 18.35:
        x = 74.95
        while x <= 78.35:
            vm = via_margin(items, net, clr, x, y, vr)
            if vm >= 0.0:
                sm = seg_margin(items, F, net, clr, pad[0], pad[1], x, y, w / 2)
                if sm >= 0.0:
                    best.append((round(vm, 3), round(sm, 3), round(x, 2), round(y, 2)))
            x += 0.05
        y += 0.05
    best.sort(reverse=True)
    for row in best[:25]:
        print("   via_margin=%.3f stub_margin=%.3f at (%.2f, %.2f)" % row)
    print(f"   total legal: {len(best)}")
