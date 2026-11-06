"""Fine-grid (0.125 mm) single-layer A* with exact-shape clearance,
for hand-scale ties the lattice router refuses: from a start pad to
goal pads on one layer. Emits shortcut-smoothed tracks.

Usage: grid_route.py IN OUT NET START_DESC GOAL_DESC[,GOAL_DESC...] LAYER(F|In2|B) X0 X1 Y0 Y1
"""
import math, sys, heapq
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
from repairg import save_checkpoint

MM = pcbnew.FromMM
CELL = 0.125
board = pcbnew.LoadBoard(sys.argv[1])
out, net = sys.argv[2], sys.argv[3]
start_desc = sys.argv[4]
goal_descs = set(sys.argv[5].split(','))
layer_name = sys.argv[6]
X0, X1, Y0, Y1 = map(float, sys.argv[7:11])
LI = {'F': 0, 'In2': 1, 'B': 2}[layer_name]
LAYER = {'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}[layer_name]
items, pad_cells = repair.build_items(board)
width, clr_net = netclass(net)
import os
if os.environ.get('GRID_W'):
    width = float(os.environ['GRID_W'])
HW = width / 2

# foreign filled zones on this layer block cells too
def zone_fills(netname_not):
    polys = []
    for z in board.Zones():
        if z.GetNetname() == netname_not: continue
        if not z.IsOnLayer(LAYER): continue
        ps = z.GetFilledPolysList(LAYER)
        for i in range(ps.OutlineCount()):
            o = ps.Outline(i)
            polys.append([(pcbnew.ToMM(o.CPoint(j).x), pcbnew.ToMM(o.CPoint(j).y))
                          for j in range(o.PointCount())])
    return polys
foreign_polys = zone_fills(net)

def in_poly(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y):
            if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside

# pad OBB tuples in build_items' format, straight from the board
pad_item = {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        pos = pcbnew.ToMM(pad.GetPosition())
        size = pcbnew.ToMM(pad.GetSize())
        pad_item[f'{ref}.{pad.GetNumber()}'] = (
            'pad', pad.GetNetname(),
            (pos[0], pos[1], size[0] / 2, size[1] / 2,
             math.radians(pad.GetOrientationDegrees())), 0.2)
GOAL_XY=None
if goal_descs and all(d.startswith('XY:') for d in goal_descs):
    d=list(goal_descs)[0]; GOAL_XY=tuple(float(v) for v in d[3:].split('_')); goal_descs=set()
XY_START=None
if start_desc.startswith('XY:'):
    XY_START=tuple(float(v) for v in start_desc[3:].split('_'))
else:
    assert start_desc in pad_item, f'start pad {start_desc} not found'

def cell_clear(x, y):
    for it in items[LI].near(LI, x, y):
        if it[1] == net: continue
        clr = max(clr_net, netclass(it[1])[1]) + 0.02
        if router.dist_to_item(it, x, y) < HW + clr: return False
    # Foreign zone fills do NOT block tracks: the refill carves the
    # pour around foreign copper at the zone's own clearance (the
    # heal item model, which never includes fills, is the authority).
    return True

def near_item(desc, x, y, tol):
    it = pad_item[desc]
    return router.dist_to_item(it, x, y) <= tol

NX = int((X1 - X0) / CELL) + 1
NY = int((Y1 - Y0) / CELL) + 1
def cell_xy(i, j): return (X0 + i * CELL, Y0 + j * CELL)
starts, goals = [], []
passable = {}
for i in range(NX):
    for j in range(NY):
        x, y = cell_xy(i, j)
        s = (math.hypot(x-XY_START[0], y-XY_START[1]) <= 0.07) if XY_START else near_item(start_desc, x, y, 0.05)
        g = (math.hypot(x-GOAL_XY[0], y-GOAL_XY[1]) <= 0.07) if GOAL_XY else any(near_item(d, x, y, 0.05) for d in goal_descs if d in pad_item)
        if not g and 'ANYCOPPER' in goal_descs:
            for it in items[LI].near(LI, x, y):
                if it[1] == net and it[0] in ('seg', 'via') and \
                        router.dist_to_item(it, x, y) <= 0.02 and \
                        (not XY_START or math.hypot(x-XY_START[0], y-XY_START[1]) > 2.0):
                    g = True; break
        if s: starts.append((i, j))
        if g: goals.append((i, j))
        passable[(i, j)] = s or g or cell_clear(x, y)
goal_set = set(goals)
print(f'grid {NX}x{NY} starts={len(starts)} goals={len(goals)} passable={sum(passable.values())}')
assert starts and goals, 'no start/goal cells'

def heur(i, j):
    return min(math.hypot(i - gi, j - gj) for gi, gj in goals) * CELL
open_h = [(heur(*s), 0.0, s) for s in starts]
heapq.heapify(open_h)
came = {s: None for s in starts}
gscore = {s: 0.0 for s in starts}
found = None
while open_h:
    f, g, cur = heapq.heappop(open_h)
    if cur in goal_set: found = cur; break
    if g > gscore.get(cur, 1e18): continue
    ci, cj = cur
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0: continue
            nb = (ci + di, cj + dj)
            if nb not in passable or not passable[nb]: continue
            ng = g + CELL * (1.4142 if di and dj else 1.0)
            if ng < gscore.get(nb, 1e18):
                gscore[nb] = ng; came[nb] = cur
                heapq.heappush(open_h, (ng + heur(*nb), ng, nb))
if not found:
    print('grid A*: NO PATH'); sys.exit(1)
path = []
cur = found
while cur: path.append(cur); cur = came[cur]
path.reverse()
pts = [cell_xy(*c) for c in path]
print('raw path cells:', len(pts), 'length', round(gscore[found], 2), 'mm')

def seg_ok(a, b):
    steps = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.08))
    for k in range(steps + 1):
        x = a[0] + (b[0] - a[0]) * k / steps
        y = a[1] + (b[1] - a[1]) * k / steps
        if (math.hypot(x-XY_START[0], y-XY_START[1]) <= 0.07) if XY_START else near_item(start_desc, x, y, 0.05): continue
        if GOAL_XY:
            if math.hypot(x-GOAL_XY[0], y-GOAL_XY[1]) <= 0.07: continue
        elif any(near_item(d, x, y, 0.05) for d in goal_descs if d in pad_item): continue
        if not cell_clear(x, y): return False
    return True

# greedy shortcut smoothing
smooth = [pts[0]]
i = 0
while i < len(pts) - 1:
    j = len(pts) - 1
    while j > i + 1 and not seg_ok(pts[i], pts[j]): j -= 1
    smooth.append(pts[j]); i = j
print('smoothed segments:', len(smooth) - 1)
nobj = board.FindNet(net)
for a, b in zip(smooth, smooth[1:]):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(width)); t.SetLayer(LAYER); t.SetNet(nobj)
    board.Add(t)
save_checkpoint(board, out)
print('saved', out)
