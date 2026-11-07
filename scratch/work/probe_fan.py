import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass
from router6 import seg_margin, via_margin, via_size, BEND_DS, SAFE
b = pcbnew.LoadBoard('scratch/work/t_aa8.kicad_pcb')
items, pad_cells = repair.build_items(b)
print("SAFE =", SAFE, "layers in items:", sorted(items.keys()))
for net, anchors in [('ULPI_DIR', [(75.92, 17.42), (74.65, 19.25)]),
                     ('ULPI_NXT', [(74.95, 17.50)])]:
    w, clr = netclass(net)
    vr = via_size(w)[0] / 2
    for (ax, ay) in anchors:
        vm = via_margin(items, net, clr, ax, ay, vr)
        print(f"{net} anchor ({ax},{ay}) w={w} vr={vr} via_margin={vm:+.3f}")
        for li in sorted(items.keys()):
            rays = []
            for (ux, uy) in ((1,0),(-1,0),(0,1),(0,-1)):
                ok = []
                for d in BEND_DS:
                    m = seg_margin(items, li, net, clr, ax, ay, ax+ux*d, ay+uy*d, w/2)
                    ok.append(f"{d}:{m:+.2f}")
                rays.append(' '.join(ok))
            for r, lab in zip(rays, 'ESWN'):
                print(f"   L{li} {lab}: {r}")
