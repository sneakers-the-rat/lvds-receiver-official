#!/usr/bin/env python3
"""GND pour stitching for the re-placed board.

The F.Cu GND pour is fragmented: 16 filled outlines, 16 single GND
pads stranded off any fill, and the HV/front-end pockets have no
F fill at all -- while the B.Cu (and In1) pour is one continuous
outline. Every stranded group and every orphan island therefore
gets the same treatment: a 0.6/0.3 GND via down to the B pour,
plus a short F stub from the pad to its via where the group is a
pad. Via spots are validated against the router's item model
(repair.build_items, all routed layers) with exact OBB/segment
distances, plus raw checks against In1 tracks and foreign zone
fills, at netclass clearance + margin. Zones are refilled on save
(repairg.save_checkpoint), and KiCad DRC is the referee afterwards.

Run: xvfb-run -a python3 scratch/gnd_stitch.py IN OUT
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

board = pcbnew.LoadBoard(sys.argv[1])
out = sys.argv[2]
items, pad_cells = repair.build_items(board)
gnd_clr = netclass('GND')[1]

# ---- filled polygons (point-in-poly for island work) ------------
def zone_fills(netname):
    fills = {}
    for z in board.Zones():
        if z.GetNetname() != netname:
            continue
        for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if not z.IsOnLayer(l):
                continue
            polys = z.GetFilledPolysList(l)
            lst = []
            for i in range(polys.OutlineCount()):
                o = polys.Outline(i)
                lst.append([(pcbnew.ToMM(o.CPoint(j).x),
                             pcbnew.ToMM(o.CPoint(j).y))
                            for j in range(o.PointCount())])
            fills.setdefault(l, []).extend(lst)
    return fills

gnd_fills = zone_fills('GND')
foreign_fills = {}
for z in board.Zones():
    if z.GetNetname() != 'GND':
        foreign_fills.update(zone_fills(z.GetNetname()))

def in_poly(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y):
            if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside

def in_fills(x, y, l, fills):
    return any(in_poly(x, y, p) for p in fills.get(l, []))

# ---- In1 foreign tracks (not in the 3-layer model) --------------
in1_foreign = []
for t in board.GetTracks():
    if t.GetLayer() == pcbnew.In1_Cu and t.GetNetname() != 'GND':
        a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
        in1_foreign.append((t.GetNetname(), a, b,
                            pcbnew.ToMM(t.GetWidth()) / 2))

def seg_pt_dist(x, y, a, b):
    px, py = x - a[0], y - a[1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, (px * dx + py * dy) / L2))
    return math.hypot(px - t * dx, py - t * dy)

def via_ok(x, y):
    """True if a GND via at (x,y) clears every foreign item."""
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
    for l, polys in foreign_fills.items():
        if in_fills(x, y, l, foreign_fills):
            return False
    return True

def stub_ok(x1, y1, x2, y2, own_desc):
    """F.Cu stub between two GND points: centreline must clear
    foreign F items by track half-width + clearance."""
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
placed_vias = []

def add_via(x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(VIA_W)); v.SetDrill(MM(VIA_D))
    v.SetNet(gnd_net)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(v)
    placed_vias.append((x, y))
    return v

def add_stub(x1, y1, x2, y2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
    t.SetWidth(MM(0.25)); t.SetLayer(pcbnew.F_Cu)
    t.SetNet(gnd_net)
    board.Add(t)

def find_via_spot(cx, cy, rmax=4.0):
    """Nearest lattice point to (cx,cy) passing via_ok, rings out."""
    r = 0.75
    while r <= rmax:
        cands = []
        n = max(8, int(2 * math.pi * r / 0.25))
        for k in range(n):
            a = 2 * math.pi * k / n
            cands.append((round(cx + r * math.cos(a), 3),
                          round(cy + r * math.sin(a), 3)))
        for x, y in cands:
            if via_ok(x, y):
                return (x, y)
        r += 0.25
    return None

# ---- 1. stranded pads (recompute: single-pad GND groups off-fill)
groups = repair.compute_groups(board)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
pad_pos = {}
for ref, fp in fps.items():
    for pad in fp.Pads():
        pad_pos[f"{ref}.{pad.GetNumber()}"] = (
            pcbnew.ToMM(pad.GetPosition().x),
            pcbnew.ToMM(pad.GetPosition().y))

stranded = []
for g in groups.get('GND', []):
    pads = [it for it in g if it.kind == 'pad']
    if len(g) != 1 or len(pads) != 1:
        continue
    x, y = pad_pos[pads[0].desc]
    if in_fills(x, y, pcbnew.F_Cu, gnd_fills) or \
       in_fills(x, y, pcbnew.B_Cu, gnd_fills):
        continue
    stranded.append((pads[0].desc, x, y))
print(f'stranded pads: {len(stranded)}')
done_pads = 0
for desc, x, y in sorted(stranded):
    spot = find_via_spot(x, y)
    if spot is None:
        print(f'  {desc}: NO via spot within 4 mm')
        continue
    if not stub_ok(x, y, spot[0], spot[1], desc):
        print(f'  {desc}: via spot {spot} but stub blocked')
        continue
    add_via(*spot)
    add_stub(x, y, spot[0], spot[1])
    done_pads += 1
    print(f'  {desc} ({x:.2f},{y:.2f}) -> via {spot}')
print(f'pad stitches placed: {done_pads}')

# ---- 2. orphan F islands: one via each, unless a via already in --
f_outlines = []
for z in board.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu):
        continue
    polys = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(polys.OutlineCount()):
        o = polys.Outline(i)
        f_outlines.append([(pcbnew.ToMM(o.CPoint(j).x),
                            pcbnew.ToMM(o.CPoint(j).y))
                           for j in range(o.PointCount())])
print(f'F outlines: {len(f_outlines)} (0 = main pour)')
isl_done = 0
for oi, poly in enumerate(f_outlines):
    if oi == 0:
        continue
    if any(in_poly(x, y, poly) for x, y in placed_vias):
        print(f'  outline {oi}: already holds a stitch via')
        isl_done += 1
        continue
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    spot = None
    # scan the outline bbox for an inside point passing via_ok,
    # nearest to centroid first
    cands = []
    gx = min(xs)
    while gx <= max(xs):
        gy = min(ys)
        while gy <= max(ys):
            if in_poly(gx, gy, poly):
                cands.append((math.hypot(gx - cx, gy - cy), gx, gy))
            gy += 0.5
        gx += 0.5
    for _, x, y in sorted(cands):
        if via_ok(x, y):
            spot = (round(x, 2), round(y, 2))
            break
    if spot is None:
        print(f'  outline {oi}: NO via spot inside')
        continue
    add_via(*spot)
    isl_done += 1
    print(f'  outline {oi}: via at {spot}')
print(f'islands stitched: {isl_done}/{len(f_outlines) - 1}')

save_checkpoint(board, out)
print('saved', out, 'vias total:', len(placed_vias))
