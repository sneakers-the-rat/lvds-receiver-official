import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew, repair, router
from router import netclass
from repairg import save_checkpoint
MM = pcbnew.FromMM
board = pcbnew.LoadBoard('scratch/stub-u10.kicad_pcb')
items, _ = repair.build_items(board)
holes = []
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition()); holes.append((p[0], p[1], pcbnew.ToMM(t.GetDrill())/2))
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.GetDrillSize().x > 0:
            p = pcbnew.ToMM(pad.GetPosition()); holes.append((p[0], p[1], pcbnew.ToMM(pad.GetDrillSize().x)/2))
in1f = []
for t in board.GetTracks():
    if t.GetLayer() == pcbnew.In1_Cu and t.GetNetname() != 'GND':
        in1f.append((t.GetNetname(), pcbnew.ToMM(t.GetStart()), pcbnew.ToMM(t.GetEnd()), pcbnew.ToMM(t.GetWidth())/2))
def spd(x, y, a, b):
    px, py = x-a[0], y-a[1]; dx, dy = b[0]-a[0], b[1]-a[1]
    L2 = dx*dx+dy*dy; t = 0.0 if L2 == 0 else max(0.0, min(1.0, (px*dx+py*dy)/L2))
    return math.hypot(px-t*dx, py-t*dy)
def via_ok(x, y):
    for hx, hy, hr in holes:
        if math.hypot(x-hx, y-hy) - 0.15 - hr < 0.25: return False
    for li in range(3):
        for it in items[li].near(li, x, y):
            if it[1] == 'GND': continue
            if router.dist_to_item(it, x, y) < 0.3 + max(0.2, netclass(it[1])[1]) + 0.05: return False
    for net, a, b, hw in in1f:
        if spd(x, y, a, b) < hw + 0.3 + max(0.2, netclass(net)[1]) + 0.05: return False
    return True
gnd = board.FindNet('GND')
for name, (ex, ey) in [('U10.5', (26.58, -2.0)), ('C29.2', (23.22, -1.5))]:
    spot = None
    for r in (0.0, 0.15, 0.25, 0.35, 0.45):
        n = 1 if r == 0 else 16
        for k in range(n):
            a = 2*math.pi*k/n
            x, y = round(ex + r*math.cos(a), 3), round(ey + r*math.sin(a), 3)
            if via_ok(x, y): spot = (x, y); break
        if spot: break
    print(name, 'stub end', (ex, ey), '-> via', spot)
    if spot:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(spot[0]), MM(spot[1])))
        v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3)); v.SetNet(gnd)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        board.Add(v)
save_checkpoint(board, 'scratch/stitch182c.kicad_pcb')
print('saved scratch/stitch182c.kicad_pcb')
