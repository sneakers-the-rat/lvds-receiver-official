"""Bent-stub pour stitch: compute a pad's free component on F at
0.125 mm grid (exact disc clearance), find a via spot inside the
component that clears every layer and lands in the In1 or B GND
plane, grid-route the stub, place via + stub. One pad per run.

Usage: component_stitch.py IN OUT PAD X0 X1 Y0 Y1
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
out, desc = sys.argv[2], sys.argv[3]
X0, X1, Y0, Y1 = map(float, sys.argv[4:8])
items, pad_cells = repair.build_items(board)
width, clr_net = netclass('GND'); HW = width / 2
VIA_R = 0.3

# --- via validation machinery (from island_stitch) ---
def zone_fills(netname):
    fills = {}
    for z in board.Zones():
        if z.GetNetname() != netname: continue
        for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if not z.IsOnLayer(l): continue
            polys = z.GetFilledPolysList(l)
            lst = []
            for i in range(polys.OutlineCount()):
                o = polys.Outline(i)
                lst.append([(pcbnew.ToMM(o.CPoint(j).x), pcbnew.ToMM(o.CPoint(j).y))
                            for j in range(o.PointCount())])
            fills.setdefault(l, []).extend(lst)
    return fills
foreign_fills = {}
for z in board.Zones():
    if z.GetNetname() != 'GND':
        for l, ps in zone_fills(z.GetNetname()).items():
            foreign_fills.setdefault(l, []).extend(ps)
def in_poly(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y):
            if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: inside = not inside
    return inside
def in_fills(x, y, l, fills): return any(in_poly(x, y, p) for p in fills.get(l, []))
plane_polys = {}
for z in board.Zones():
    if z.GetNetname() != 'GND': continue
    for l in (pcbnew.In1_Cu, pcbnew.B_Cu):
        if z.IsOnLayer(l): plane_polys[l] = z.GetFilledPolysList(l)
in1_foreign = []
for t in board.GetTracks():
    if t.GetLayer() == pcbnew.In1_Cu and t.GetNetname() != 'GND':
        a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
        in1_foreign.append((t.GetNetname(), a, b, pcbnew.ToMM(t.GetWidth()) / 2))
def seg_pt_dist(x, y, a, b):
    px, py = x - a[0], y - a[1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, (px * dx + py * dy) / L2))
    return math.hypot(px - t * dx, py - t * dy)
holes = []
for fp in board.GetFootprints():
    for pad in fp.Pads():
        d = pcbnew.ToMM(pad.GetDrillSize().x)
        if d > 0 and pad.GetNetname() != 'GND':
            p = pcbnew.ToMM(pad.GetPosition()); holes.append((p[0], p[1], d / 2))
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() != 'GND':
        p = pcbnew.ToMM(t.GetPosition()); holes.append((p[0], p[1], pcbnew.ToMM(t.GetDrillValue()) / 2))
def via_ok(x, y):
    for li in range(3):
        for it in items[li].near(li, x, y):
            if it[1] == 'GND': continue
            clr = max(clr_net, netclass(it[1])[1]) + 0.05
            if router.dist_to_item(it, x, y) < VIA_R + clr: return False
    for net, a, b, hw in in1_foreign:
        clr = max(clr_net, netclass(net)[1]) + 0.05
        if seg_pt_dist(x, y, a, b) < hw + VIA_R + clr: return False
    for l in foreign_fills:
        if in_fills(x, y, l, foreign_fills): return False
    for hx, hy, hr in holes:
        if math.hypot(x - hx, y - hy) < 0.15 + hr + 0.25: return False
    return True

# --- grid component of the pad on F ---
pad_t = None
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if f'{fp.GetReference()}.{pad.GetNumber()}' == desc:
            pos = pcbnew.ToMM(pad.GetPosition()); size = pcbnew.ToMM(pad.GetSize())
            pad_t = ('pad', 'GND', (pos[0], pos[1], size[0] / 2, size[1] / 2,
                                    math.radians(pad.GetOrientationDegrees())), 0.2)
assert pad_t
def cell_clear(x, y):
    for it in items[0].near(0, x, y):
        if it[1] == 'GND': continue
        clr = max(clr_net, netclass(it[1])[1]) + 0.02
        if router.dist_to_item(it, x, y) < HW + clr: return False
    return True
NX = int((X1 - X0) / CELL) + 1; NY = int((Y1 - Y0) / CELL) + 1
def cxy(i, j): return (X0 + i * CELL, Y0 + j * CELL)
passable = {}
starts = []
for i in range(NX):
    for j in range(NY):
        x, y = cxy(i, j)
        s = router.dist_to_item(pad_t, x, y) <= 0.05
        if s: starts.append((i, j))
        passable[(i, j)] = s or cell_clear(x, y)
comp = set(starts); stack = list(starts)
while stack:
    i, j = stack.pop()
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        nb = (i + di, j + dj)
        if nb not in comp and passable.get(nb):
            comp.add(nb); stack.append(nb)
print(f'{desc}: component {len(comp)} cells')
# via candidates inside the component on a 0.25 lattice
cands = []
for (i, j) in comp:
    x, y = cxy(i, j)
    if abs(x * 4 - round(x * 4)) > 1e-6 or abs(y * 4 - round(y * 4)) > 1e-6: continue
    pt = pcbnew.VECTOR2I(MM(x), MM(y))
    if not any(p.Contains(pt) for p in plane_polys.values()): continue
    if via_ok(x, y): cands.append((x, y))
print('via candidates in component:', len(cands))
if not cands:
    print('NO VIA SPOT'); sys.exit(1)
# grid A* pad -> nearest candidate
goal_set = set()
for (x, y) in cands:
    goal_set.add((round((x - X0) / CELL), round((y - Y0) / CELL)))
def heur(i, j): return min(math.hypot(i - gi, j - gj) for gi, gj in goal_set) * CELL
open_h = [(heur(*s), 0.0, s) for s in starts]; heapq.heapify(open_h)
came = {s: None for s in starts}; gscore = {s: 0.0 for s in starts}
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
            if not passable.get(nb): continue
            ng = g + CELL * (1.4142 if di and dj else 1.0)
            if ng < gscore.get(nb, 1e18):
                gscore[nb] = ng; came[nb] = cur
                heapq.heappush(open_h, (ng + heur(*nb), ng, nb))
assert found, 'no grid path to via candidate'
path = []; cur = found
while cur: path.append(cur); cur = came[cur]
path.reverse()
pts = [cxy(*c) for c in path]
def seg_ok(a, b):
    steps = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.08))
    for k in range(steps + 1):
        x = a[0] + (b[0] - a[0]) * k / steps; y = a[1] + (b[1] - a[1]) * k / steps
        if router.dist_to_item(pad_t, x, y) <= 0.05: continue
        if not cell_clear(x, y): return False
    return True
smooth = [pts[0]]; i = 0
while i < len(pts) - 1:
    j = len(pts) - 1
    while j > i + 1 and not seg_ok(pts[i], pts[j]): j -= 1
    smooth.append(pts[j]); i = j
vx, vy = pts[-1]
net = board.FindNet('GND')
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy)))
v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3)); v.SetNet(net)
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
board.Add(v)
for a, b in zip(smooth, smooth[1:]):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(width)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net)
    board.Add(t)
print(f'{desc}: via at ({vx},{vy}), stub segments {len(smooth) - 1}')
save_checkpoint(board, out)
print('saved', out)
