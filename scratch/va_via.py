"""Necked stub + via for a sealed pad of NET: search a candidate box
for a via that clears all layers (exact model), with a straight stub
from the pad to the via (exact seg test). Usage:
va_via.py IN OUT NET PAD X0 X1 Y0 Y1"""
import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
from repairg import save_checkpoint
MM = pcbnew.FromMM
board = pcbnew.LoadBoard(sys.argv[1])
out, net_name, desc = sys.argv[2], sys.argv[3], sys.argv[4]
X0, X1, Y0, Y1 = map(float, sys.argv[5:9])
items, pad_cells = repair.build_items(board)
width, clr_net = netclass(net_name)
VIA_R = 0.3
pad_t, pad_pos = None, None
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if f'{fp.GetReference()}.{pad.GetNumber()}' == desc:
            pos = pcbnew.ToMM(pad.GetPosition()); size = pcbnew.ToMM(pad.GetSize())
            pad_pos = pos
            pad_t = ('pad', net_name, (pos[0], pos[1], size[0] / 2, size[1] / 2,
                                       math.radians(pad.GetOrientationDegrees())), 0.2)
assert pad_t
def via_ok(x, y):
    for li in range(3):
        for it in items[li].near(li, x, y):
            if it[1] == net_name: continue
            clr = max(clr_net, netclass(it[1])[1]) + 0.05
            if router.dist_to_item(it, x, y) < VIA_R + clr: return False
    return True
def stub_ok(x1, y1, x2, y2, w):
    hw = w / 2
    steps = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.06))
    for k in range(steps + 1):
        x = x1 + (x2 - x1) * k / steps; y = y1 + (y2 - y1) * k / steps
        if router.dist_to_item(pad_t, x, y) <= 0.02: continue
        for it in items[0].near(0, x, y):
            if it[1] == net_name: continue
            clr = max(clr_net, netclass(it[1])[1]) + 0.02
            if router.dist_to_item(it, x, y) < hw + clr: return False
    return True
best = None
gx = X0
while gx <= X1:
    gy = Y0
    while gy <= Y1:
        x, y = round(gx, 3), round(gy, 3)
        if via_ok(x, y) and stub_ok(pad_pos[0], pad_pos[1], x, y, 0.25):
            d = math.hypot(x - pad_pos[0], y - pad_pos[1])
            if best is None or d < best[0]: best = (d, x, y)
        gy += 0.125
    gx += 0.125
if not best:
    print(f'{desc}: NO via+stub in box'); sys.exit(1)
_, vx, vy = best
net = board.FindNet(net_name)
t = pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(MM(pad_pos[0]), MM(pad_pos[1]))); t.SetEnd(pcbnew.VECTOR2I(MM(vx), MM(vy)))
t.SetWidth(MM(0.25)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net)
board.Add(t)
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy)))
v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3)); v.SetNet(net)
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
board.Add(v)
print(f'{desc}: stub+via at ({vx},{vy})')
save_checkpoint(board, out)
print('saved', out)
