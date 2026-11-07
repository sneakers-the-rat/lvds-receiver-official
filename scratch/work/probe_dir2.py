import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import wx
_app = wx.App(False)
import pcbnew
import repair, router
from router import netclass
from router6 import via_margin, via_size
b = pcbnew.LoadBoard('scratch/work/t_aa6.kicad_pcb')
items, pad_cells = repair.build_items(b)
net = 'ULPI_DIR'
w, clr = netclass(net)
vr = via_size(w)[0] / 2
pts = []
y = 16.90
while y <= 21.05:
    x = 74.60
    while x <= 79.00:
        vm = via_margin(items, net, clr, x, y, vr)
        if vm >= 0.0:
            pts.append((round(vm, 3), round(x, 2), round(y, 2)))
        x += 0.05
    y += 0.05
pts.sort(reverse=True)
print(f"{net}: {len(pts)} via-legal in wide box; best 20:")
for p in pts[:20]: print("   vm=%.3f at (%.2f, %.2f)" % p)
# blockers at sample points
for (px, py) in [(76.90, 17.90), (77.40, 17.60), (76.40, 17.90), (75.92, 17.42)]:
    print(f"-- blockers near ({px},{py}):")
    for li in range(3):
        for it in items[li].near(li, px, py):
            if it[1] == net: continue
            need = vr + max(clr, netclass(it[1])[1])
            d = router.dist_to_item(it, px, py)
            if d < need + 0.35:
                print(f"   L{li} {it[1]}({it[0]}) d={d:.3f} need={need:.3f} margin={d-need:+.3f}")
