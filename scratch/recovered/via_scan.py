import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}
board = pcbnew.LoadBoard(sys.argv[1])
net = sys.argv[2]
x0, x1, y0, y1, step = [float(a) for a in sys.argv[3:8]]
items = build_items(board)
print(f"{len(items)} items; scanning via sites for {net} in x[{x0},{x1}] y[{y0},{y1}] step {step}")
clear = []
y = y0
while y <= y1 + 1e-9:
    x = x0
    while x <= x1 + 1e-9:
        disc = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x), MM(y)),
                                    pcbnew.VECTOR2I(MM(x), MM(y)), MM(0.6))
        bad = 0
        for kind, n2, l2, s2, desc in items:
            if n2 == net or kind == 'zone':
                continue
            shared = ALL & l2
            if not shared:
                continue
            need = need_for(net, n2, shared)
            if disc.Collide(s2, MM(need - 0.001 + 0.02)):
                bad += 1
                break
        if not bad:
            clear.append((round(x, 2), round(y, 2)))
        x += step
    y += step
print(f"clear via sites: {len(clear)}")
for c in clear:
    print("  ", c)
