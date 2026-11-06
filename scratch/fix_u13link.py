import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
from repairg import save_checkpoint
MM = pcbnew.FromMM
mm = lambda v: v / 1e6
board = pcbnew.LoadBoard(sys.argv[1])
items, pad_cells = repair.build_items(board)
# diagnostic: model distance from the violating point to U13.8's pad item
for it in items[0].near(0, 41.125, 49.625):
    if it[1] == 'GND':
        print('model dist to GND item', it[0], '=', round(router.dist_to_item(it, 41.125, 49.625), 3))
# rip all +VA tracks in the U13 box
victims = []
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != '+VA': continue
    s, e = t.GetStart(), t.GetEnd()
    if 39.5 < mm(s.x) < 42.5 and 48 < mm(s.y) < 51: victims.append(t)
print('ripping +VA tracks near U13:', len(victims))
for t in victims: board.Remove(t)
board.Save('/tmp/u13rip.kicad_pcb')
board = pcbnew.LoadBoard('/tmp/u13rip.kicad_pcb')
items, pad_cells = repair.build_items(board)
width, clr_net = netclass('+VA'); HW = width / 2
def seg_ok(a, b):
    steps = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.05))
    for k in range(steps + 1):
        x = a[0] + (b[0] - a[0]) * k / steps; y = a[1] + (b[1] - a[1]) * k / steps
        for it in items[0].near(0, x, y):
            if it[1] == '+VA': continue
            clr = max(clr_net, netclass(it[1])[1]) + 0.02
            d = router.dist_to_item(it, x, y)
            if d < HW + clr: return False, (round(x, 2), round(y, 2), it[1], round(d, 3), round(HW + clr, 3))
    return True, None
pts = [(41.30, 49.25), (40.30, 49.25), (40.30, 49.75), (41.30, 49.75)]
for a, b in zip(pts, pts[1:]):
    ok, why = seg_ok(a, b)
    print(a, '->', b, 'OK' if ok else f'BLOCKED {why}')
    assert ok
net = board.FindNet('+VA')
for a, b in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(width)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net)
    board.Add(t)
save_checkpoint(board, sys.argv[2])
print('saved', sys.argv[2])
