#!/usr/bin/env python3
"""GND stitch round 2, on the round-1 board.

Fixes the three leftovers of round 1:
  a. the C4.2 via sat 0.75 mm from C4's own PTH hole
     (hole_near_hole x2): remove it and re-place with an explicit
     drill-edge >= 0.25 mm test against every existing hole;
  b. U10.5 and C29.2 found via spots whose straight stubs were
     blocked: joint search -- a spot counts only if via AND stub
     both clear, with an L-shaped two-segment stub as fallback;
  c. six F fill slivers too narrow for an interior via: place the
     via overlapping the outline edge (centre within via radius
     of the polygon) so the refill ties it to the fragment.

Run: xvfb-run -a python3 scratch/gnd_stitch2.py IN OUT
"""
import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
from repairg import save_checkpoint

MM = pcbnew.FromMM
VIA_W, VIA_D = 0.6, 0.3
VIA_R = VIA_W / 2
MARGIN = 0.05
HOLE_GAP = 0.25

board = pcbnew.LoadBoard(sys.argv[1])
out = sys.argv[2]
items, _ = repair.build_items(board)
gnd_clr = netclass('GND')[1]

# ---- holes --------------------------------------------------------
holes = []  # (x, y, drill_r)
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition())
        holes.append((p[0], p[1], pcbnew.ToMM(t.GetDrill()) / 2))
for fp in board.GetFootprints():
    for pad in fp.Pads():
        ds = pad.GetDrillSize()
        if ds.x > 0:
            p = pcbnew.ToMM(pad.GetPosition())
            holes.append((p[0], p[1], pcbnew.ToMM(ds.x) / 2))

def hole_ok(x, y, skip=None):
    for hx, hy, hr in holes:
        if skip and abs(hx - skip[0]) < 0.01 and abs(hy - skip[1]) < 0.01:
            continue
        if math.hypot(x - hx, y - hy) - VIA_D / 2 - hr < HOLE_GAP:
            return False
    return True

# ---- fills --------------------------------------------------------
def gnd_f_outlines():
    res = []
    for z in board.Zones():
        if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu):
            continue
        polys = z.GetFilledPolysList(pcbnew.F_Cu)
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            res.append([(pcbnew.ToMM(o.CPoint(j).x),
                         pcbnew.ToMM(o.CPoint(j).y))
                        for j in range(o.PointCount())])
    return res

def in_poly(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y):
            if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside

def pt_poly_dist(x, y, poly):
    d = 1e9
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
        px, py = x - x1, y - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, (px * dx + py * dy) / L2))
        d = min(d, math.hypot(px - t * dx, py - t * dy))
    return d

# ---- item-model clearance -----------------------------------------
in1_foreign = []
for t in board.GetTracks():
    if t.GetLayer() == pcbnew.In1_Cu and t.GetNetname() != 'GND':
        in1_foreign.append((t.GetNetname(), pcbnew.ToMM(t.GetStart()),
                            pcbnew.ToMM(t.GetEnd()),
                            pcbnew.ToMM(t.GetWidth()) / 2))

def seg_pt_dist(x, y, a, b):
    px, py = x - a[0], y - a[1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, (px * dx + py * dy) / L2))
    return math.hypot(px - t * dx, py - t * dy)

def via_ok(x, y):
    if not hole_ok(x, y):
        return False
    for li in range(3):
        for it in items[li].near(li, x, y):
            if it[1] == 'GND':
                continue
            clr = max(gnd_clr, netclass(it[1])[1]) + MARGIN
            if router.dist_to_item(it, x, y) < VIA_R + clr:
                return False
    for net, a, b, hw in in1_foreign:
        clr = max(gnd_clr, netclass(net)[1]) + MARGIN
        if seg_pt_dist(x, y, a, b) < hw + VIA_R + clr:
            return False
    return True

def stub_ok(x1, y1, x2, y2):
    hw = 0.25 / 2
    steps = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.2))
    for i in range(steps + 1):
        x = x1 + (x2 - x1) * i / steps
        y = y1 + (y2 - y1) * i / steps
        for it in items[0].near(0, x, y):
            if it[1] == 'GND':
                continue
            clr = max(gnd_clr, netclass(it[1])[1]) + MARGIN
            if router.dist_to_item(it, x, y) < hw + clr:
                return False
    return True

gnd_net = board.FindNet('GND')
placed = []

def add_via(x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(VIA_W)); v.SetDrill(MM(VIA_D))
    v.SetNet(gnd_net); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(v)
    placed.append((x, y))
    holes.append((x, y, VIA_D / 2))

def add_stub(x1, y1, x2, y2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
    t.SetWidth(MM(0.25)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd_net)
    board.Add(t)

def ring_spots(cx, cy, rmax):
    r = 0.75
    while r <= rmax:
        n = max(16, int(2 * math.pi * r / 0.2))
        for k in range(n):
            a = 2 * math.pi * k / n
            yield (round(cx + r * math.cos(a), 3),
                   round(cy + r * math.sin(a), 3))
        r += 0.25

# ---- a/b. re-place the three pads (C4.2's bad via already removed
# by scratch/rm_c4via.py into the input board; NOTE: no board.Remove
# in this process -- KiCad 8 proxies break after Remove, so all
# removals happen in their own load/save cycle) ---------------------
for desc, (x, y) in [('C4.2', (26.75, 18.0)),
                     ('U10.5', (25.35, -2.0)),
                     ('C29.2', (22.27, -1.5))]:
    got = None
    for sx, sy in ring_spots(x, y, 5.0):
        if via_ok(sx, sy) and stub_ok(x, y, sx, sy):
            got = (sx, sy, 'straight'); break
    if got is None:
        # L-stub: via spot anywhere clear; elbow at (sx, y) or (x, sy)
        for sx, sy in ring_spots(x, y, 5.0):
            if not via_ok(sx, sy):
                continue
            for ex, ey in ((sx, y), (x, sy)):
                if stub_ok(x, y, ex, ey) and stub_ok(ex, ey, sx, sy):
                    got = (sx, sy, f'L via ({ex:.2f},{ey:.2f})')
                    add_via(sx, sy)
                    add_stub(x, y, ex, ey); add_stub(ex, ey, sx, sy)
                    break
            if got: break
    elif got:
        add_via(got[0], got[1]); add_stub(x, y, got[0], got[1])
    print(f'{desc}: {got}')
    items, _ = repair.build_items(board)

# ---- c. sliver islands: edge-overlap vias --------------------------
outlines = gnd_f_outlines()
print(f'F outlines now: {len(outlines)}')
via_pts = [(pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y))
           for t in board.GetTracks()
           if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == 'GND']
for oi, poly in enumerate(outlines):
    if oi == 0:
        continue
    if any(in_poly(x, y, poly) for x, y in via_pts):
        continue
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    cands = []
    gx = min(xs) - 0.3
    while gx <= max(xs) + 0.3:
        gy = min(ys) - 0.3
        while gy <= max(ys) + 0.3:
            d = 0.0 if in_poly(gx, gy, poly) else pt_poly_dist(gx, gy, poly)
            if d <= VIA_R - 0.02:
                cands.append((math.hypot(gx - cx, gy - cy), gx, gy))
            gy += 0.25
        gx += 0.25
    spot = None
    for _, x, y in sorted(cands):
        if via_ok(round(x, 2), round(y, 2)):
            spot = (round(x, 2), round(y, 2)); break
    if spot:
        add_via(*spot); via_pts.append(spot)
        items, _ = repair.build_items(board)
        print(f'  outline {oi}: edge via {spot}')
    else:
        print(f'  outline {oi}: STILL no spot')

save_checkpoint(board, out)
print('saved', out)
