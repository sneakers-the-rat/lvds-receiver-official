import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
src = open('scratch/island_stitch.py').read()
head = src.split('gnd_net = ')[0]
head = head.replace("board = pcbnew.LoadBoard(sys.argv[1])", "board = pcbnew.LoadBoard(sys.argv[1])")
exec(head)
from repairg import save_checkpoint

def stub_ok(x1, y1, x2, y2):
    hw = 0.25 / 2
    steps = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.15))
    for i in range(steps + 1):
        x = x1 + (x2 - x1) * i / steps
        y = y1 + (y2 - y1) * i / steps
        for it in items[0].near(0, x, y):
            if it[1] == 'GND': continue
            clr = max(gnd_clr, netclass(it[1])[1]) + MARGIN
            if router.dist_to_item(it, x, y) < hw + clr: return False
    return True

gnd_net = board.FindNet('GND')
islands = [(7, (71.3, 73.2, 23.7, 27.1)), (10, (74.9, 77.8, 7.0, 10.9)),
           (12, (78.8, 80.4, 3.8, 6.7)), (13, (73.6, 73.9, 3.8, 5.5))]
f_outlines = gnd_fills.get(pcbnew.F_Cu, [])
for idx, (x0, x1, y0, y1) in islands:
    # island outline = F outline whose bbox is closest to the island bbox
    poly = None; best = 1e9
    for p in f_outlines:
        xs = [q[0] for q in p]; ys = [q[1] for q in p]
        d = abs(min(xs) - x0) + abs(max(xs) - x1) + abs(min(ys) - y0) + abs(max(ys) - y1)
        if d < best: best = d; poly = p
    inside_pts = []
    gx = x0
    while gx <= x1:
        gy = y0
        while gy <= y1:
            if in_poly(round(gx, 3), round(gy, 3), poly): inside_pts.append((round(gx, 3), round(gy, 3)))
            gy += 0.125
        gx += 0.125
    if not inside_pts:
        print(f'island {idx}: no interior samples (bbox match d={best:.2f})'); continue
    # candidate vias: rings around the bbox, nearest first
    ccx, ccy = (x0 + x1) / 2, (y0 + y1) / 2
    cands = []
    r = 0.4
    while r <= 3.0:
        n = max(16, int(2 * math.pi * r / 0.125))
        for k in range(n):
            a = 2 * math.pi * k / n
            cands.append((round(ccx + r * math.cos(a), 3), round(ccy + r * math.sin(a), 3)))
        r += 0.2
    done = False
    for x, y in cands:
        if not in1_polys.Contains(pcbnew.VECTOR2I(MM(x), MM(y))): continue
        if not via_ok(x, y): continue
        # nearest island-interior point to the via
        inside_pts.sort(key=lambda p: math.hypot(p[0] - x, p[1] - y))
        for px, py in inside_pts[:14]:
            if math.hypot(px - x, py - y) < 0.35: continue
            if stub_ok(x, y, px, py):
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
                v.SetWidth(MM(VIA_W)); v.SetDrill(MM(VIA_D)); v.SetNet(gnd_net)
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                board.Add(v)
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(MM(x), MM(y)))
                t.SetEnd(pcbnew.VECTOR2I(MM(px), MM(py)))
                t.SetWidth(MM(0.25)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd_net)
                board.Add(t)
                print(f'island {idx}: via ({x},{y}) + track to ({px},{py})')
                done = True
                break
        if done: break
    if not done: print(f'island {idx}: NO via+track placement')
save_checkpoint(board, sys.argv[2])
print('saved', sys.argv[2])
