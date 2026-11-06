import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
from repairg import save_checkpoint
MM = pcbnew.FromMM
mm = lambda v: v / 1e6
board = pcbnew.LoadBoard(sys.argv[1])
victims = []
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != '+VA': continue
    s, e = t.GetStart(), t.GetEnd()
    if 39.5 < mm(s.x) < 42.5 and 48 < mm(s.y) < 51: victims.append(t)
print('ripping +VA tracks near U13:', len(victims))
for t in victims: board.Remove(t)
board.Save('/tmp/u13rip2.kicad_pcb')
board = pcbnew.LoadBoard('/tmp/u13rip2.kicad_pcb')
items, pad_cells = repair.build_items(board)
clr_net = netclass('+VA')[1]
def seg_ok(a, b, w):
    hw = w / 2
    steps = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.05))
    for k in range(steps + 1):
        x = a[0] + (b[0] - a[0]) * k / steps; y = a[1] + (b[1] - a[1]) * k / steps
        for it in items[0].near(0, x, y):
            if it[1] == '+VA': continue
            clr = max(clr_net, netclass(it[1])[1])
            d = router.dist_to_item(it, x, y)
            if d < hw + clr: return False, (round(x, 2), round(y, 2), it[1], round(d, 3), round(hw + clr, 3))
    return True, None
segs = [((41.30, 49.25), (42.30, 49.25), 0.2),
        ((41.30, 49.75), (42.30, 49.75), 0.2),
        ((42.30, 49.25), (42.30, 49.75), 0.6)]
net = board.FindNet('+VA')
for a, b, w in segs:
    ok, why = seg_ok(a, b, w)
    print(a, '->', b, f'w{w}', 'OK' if ok else f'BLOCKED {why}')
    assert ok
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(w)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net)
    board.Add(t)
save_checkpoint(board, sys.argv[2])
print('saved', sys.argv[2])
