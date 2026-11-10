import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
from repairg import save_checkpoint
MM = pcbnew.FromMM
mm = lambda v: v / 1e6
board = pcbnew.LoadBoard(sys.argv[1])
# 1. rip every HV_VC2 track in the local box (stale pre-move copper + the bad grid route)
victims = []
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != 'HV_VC2': continue
    s, e = t.GetStart(), t.GetEnd()
    if 18 < mm(s.x) < 26 and -6 < mm(s.y) < 2: victims.append(t)
print('ripping HV_VC2 tracks in box:', len(victims))
for t in victims: board.Remove(t)
board.Save('/tmp/vc2rip.kicad_pcb')
board = pcbnew.LoadBoard('/tmp/vc2rip.kicad_pcb')
items, pad_cells = repair.build_items(board)
width, clr_net = netclass('HV_VC2'); HW = width / 2
def seg_ok(a, b):
    steps = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.08))
    for k in range(steps + 1):
        x = a[0] + (b[0] - a[0]) * k / steps
        y = a[1] + (b[1] - a[1]) * k / steps
        for it in items[0].near(0, x, y):
            if it[1] == 'HV_VC2': continue
            clr = max(clr_net, netclass(it[1])[1]) + 0.02
            if router.dist_to_item(it, x, y) < HW + clr: return False, (x, y, it[1])
    return True, None
pts = [(20.73, -1.00), (20.05, -1.00), (20.05, -3.85), (23.0, -3.85), (23.57, -3.00)]
for a, b in zip(pts, pts[1:]):
    ok, why = seg_ok(a, b)
    print(a, '->', b, 'OK' if ok else f'BLOCKED at {why}')
    assert ok
net = board.FindNet('HV_VC2')
for a, b in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(width)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net)
    board.Add(t)
save_checkpoint(board, sys.argv[2])
print('saved', sys.argv[2])
