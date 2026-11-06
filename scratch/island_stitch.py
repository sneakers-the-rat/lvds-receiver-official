import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
from repairg import save_checkpoint

MM = pcbnew.FromMM
VIA_W, VIA_D, VIA_R, MARGIN = 0.6, 0.3, 0.3, 0.05
board = pcbnew.LoadBoard(sys.argv[1])
out = sys.argv[2]
items, pad_cells = repair.build_items(board)
gnd_clr = netclass('GND')[1]

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

gnd_fills = zone_fills('GND')
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
            if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside

def in_fills(x, y, l, fills):
    return any(in_poly(x, y, p) for p in fills.get(l, []))

in1_polys = None
for z in board.Zones():
    if z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.In1_Cu):
        in1_polys = z.GetFilledPolysList(pcbnew.In1_Cu)

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

# foreign drill holes (pads with drill + vias) for hole_near_hole guard
holes = []
for fp in board.GetFootprints():
    for pad in fp.Pads():
        d = pcbnew.ToMM(pad.GetDrillSize().x)
        if d > 0 and pad.GetNetname() != 'GND':
            p = pcbnew.ToMM(pad.GetPosition())
            holes.append((p[0], p[1], d / 2))
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() != 'GND':
        p = pcbnew.ToMM(t.GetPosition())
        holes.append((p[0], p[1], pcbnew.ToMM(t.GetDrillValue()) / 2))

def via_ok(x, y):
    for li in range(3):
        for it in items[li].near(li, x, y):
            if it[1] == 'GND': continue
            clr = max(gnd_clr, netclass(it[1])[1]) + MARGIN
            if router.dist_to_item(it, x, y) < VIA_R + clr: return False
    for net, a, b, hw in in1_foreign:
        clr = max(gnd_clr, netclass(net)[1]) + MARGIN
        if seg_pt_dist(x, y, a, b) < hw + VIA_R + clr: return False
    for l, polys in foreign_fills.items():
        if in_fills(x, y, l, foreign_fills): return False
    for hx, hy, hr in holes:
        if math.hypot(x - hx, y - hy) < VIA_D / 2 + hr + 0.25: return False
    return True

def ring_touches_F_fill(x, y):
    for k in range(9):
        a = 2 * math.pi * k / 8
        if in_fills(x + 0.22 * math.cos(a), y + 0.22 * math.sin(a), pcbnew.F_Cu, gnd_fills):
            return True
    return in_fills(x, y, pcbnew.F_Cu, gnd_fills)

gnd_net = board.FindNet('GND')
islands = [(7, (71.3, 73.2, 23.7, 27.1)), (10, (74.9, 77.8, 7.0, 10.9)),
           (11, (65.3, 67.1, 6.1, 6.9)), (12, (78.8, 80.4, 3.8, 6.7)),
           (13, (73.6, 73.9, 3.8, 5.5))]
for idx, (x0, x1, y0, y1) in islands:
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cands = []
    gx = x0 - 0.35
    while gx <= x1 + 0.35:
        gy = y0 - 0.35
        while gy <= y1 + 0.35:
            cands.append((round(gx, 3), round(gy, 3)))
            gy += 0.125
        gx += 0.125
    cands.sort(key=lambda p: math.hypot(p[0] - cx, p[1] - cy))
    spot = None
    for x, y in cands:
        if not ring_touches_F_fill(x, y): continue
        if not in1_polys.Contains(pcbnew.VECTOR2I(MM(x), MM(y))): continue
        if via_ok(x, y):
            spot = (x, y); break
    if spot:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(spot[0]), MM(spot[1])))
        v.SetWidth(MM(VIA_W)); v.SetDrill(MM(VIA_D)); v.SetNet(gnd_net)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        board.Add(v)
        print(f'island {idx}: via at {spot}')
    else:
        print(f'island {idx}: NO via spot found')
save_checkpoint(board, out)
print('saved', out)
