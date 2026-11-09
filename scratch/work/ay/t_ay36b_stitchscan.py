import sys, math
sys.path.insert(0, 'scratch/work/ax')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp251.kicad_pcb')
F = pcbnew.F_Cu

def mm(v):
    return (v.x / 1e6, v.y / 1e6)

polys = []
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(F):
        continue
    poly = z.GetFilledPolysList(F)
    for oi in range(poly.OutlineCount()):
        o = poly.Outline(oi)
        pts = [(o.GetPoint(i).x / 1e6, o.GetPoint(i).y / 1e6)
               for i in range(o.PointCount())]
        polys.append(pts)

def in_poly(px, py, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            xin = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < xin:
                inside = not inside
    return inside

foreign = []
for t in b.GetTracks():
    if t.GetNetname() == 'GND':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        foreign.append(('via', mm(t.GetPosition()), t.GetWidth() / 2e6,
                        t.GetNetname()))
    else:
        foreign.append(('seg', (mm(t.GetStart()), mm(t.GetEnd())),
                        t.GetWidth() / 2e6, t.GetNetname()))
pads_f = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() != 'GND':
            pads_f.append((mm(p.GetPosition()),
                           (p.GetSize().x / 2e6, p.GetSize().y / 2e6),
                           p.GetNetname()))

def seg_dist(px, py, a, bb_):
    dx, dy = bb_[0] - a[0], bb_[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - a[0]) * dx +
                                              (py - a[1]) * dy) / L2))
    return math.hypot(px - (a[0] + t * dx), py - (a[1] + t * dy))

def viafit(px, py):
    worst, who = 9.9, None
    for kind, d, r, net in foreign:
        if kind == 'via':
            dd = math.hypot(px - d[0], py - d[1]) - r
        else:
            dd = seg_dist(px, py, d[0], d[1]) - r
        g = dd - 0.25 - 0.2
        if g < worst:
            worst, who = g, (net, kind)
    for (cx, cy), (hw, hh), net in pads_f:
        dd = math.hypot(max(abs(px - cx) - hw, 0.0),
                        max(abs(py - cy) - hh, 0.0))
        g = dd - 0.25 - 0.2
        if g < worst:
            worst, who = g, (net, 'pad')
    return worst, who

# target polygons: the one containing (67.0,0.6) and the one containing
# (69.5,-8.0); fall back to bbox-matched polygons if a point misses
targets = {}
for i, pts in enumerate(polys):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    bb = (round(min(xs), 1), round(max(xs), 1), round(min(ys), 1),
          round(max(ys), 1))
    if bb == (66.7, 68.1, -1.0, 1.3):
        targets['A24'] = i
    if bb == (68.2, 72.2, -0.2, 1.2):
        targets['P25'] = i
    if bb == (67.1, 72.2, -11.2, -5.4):
        targets['P28'] = i
print('target polys:', targets, flush=True)
for tag, i in targets.items():
    pts = polys[i]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    best = []
    gx = min(xs)
    while gx <= max(xs):
        gy = min(ys)
        while gy <= max(ys):
            if in_poly(gx, gy, pts):
                g, who = viafit(gx, gy)
                best.append((round(g, 3), round(gx, 2), round(gy, 2), who))
            gy += 0.25
        gx += 0.25
    best.sort(reverse=True)
    print(f'island {tag} poly {i} bbox x[{min(xs):.1f},{max(xs):.1f}] '
          f'y[{min(ys):.1f},{max(ys):.1f}] best sites:', flush=True)
    for row in best[:5]:
        print('   ', row, flush=True)
