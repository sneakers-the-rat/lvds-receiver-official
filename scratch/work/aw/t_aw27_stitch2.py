"""t_aw27: refined stitch-point search for orphan GND islands 9,10,14,23.
Per-layer gap computation for via radii 0.30/0.25/0.225/0.20; also
identify island 14's pad and the channels severing it."""
import wx
_app = wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241.kicad_pcb')
F = pcbnew.F_Cu
zone = None
for z in b.Zones():
    if z.GetNetname() == 'GND' and z.IsOnLayer(F):
        zone = z
        break
fps = zone.GetFilledPolysList(F)
polys = []
for i in range(fps.OutlineCount()):
    out = fps.Outline(i)
    pts = [(pcbnew.ToMM(out.CPoint(k).x), pcbnew.ToMM(out.CPoint(k).y))
           for k in range(out.PointCount())]
    polys.append(pts)


def inside(pts, tx, ty):
    res = False
    m = len(pts)
    for k in range(m):
        x1, y1 = pts[k]
        x2, y2 = pts[(k + 1) % m]
        if (y1 > ty) != (y2 > ty):
            xin = (x2 - x1) * (ty - y1) / (y2 - y1) + x1
            if tx < xin:
                res = not res
    return res


LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
vias = []   # (net, x, y, r, drill_r) all layers
pads = []   # (net, x, y, hw, hh) F layer, axis approx via max radius
segs = []   # (net, layer_idx, x1,y1,x2,y2, hw)
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition())
        vias.append((t.GetNetname(), p[0], p[1],
                     pcbnew.ToMM(t.GetWidth()) / 2,
                     pcbnew.ToMM(t.GetDrill()) / 2))
    else:
        a = pcbnew.ToMM(t.GetStart())
        c = pcbnew.ToMM(t.GetEnd())
        if t.GetLayer() in LAYERS:
            segs.append((t.GetNetname(), LAYERS.index(t.GetLayer()),
                         a[0], a[1], c[0], c[1],
                         pcbnew.ToMM(t.GetWidth()) / 2))
for fp in b.GetFootprints():
    for p in fp.Pads():
        pp = pcbnew.ToMM(p.GetPosition())
        sz = pcbnew.ToMM(p.GetSize())
        pads.append((p.GetNetname(), pp[0], pp[1],
                     max(sz) / 2, fp.GetReference(), p.GetNumber()))


def segdist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    tt = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return ((px - x1 - tt * dx) ** 2 + (py - y1 - tt * dy) ** 2) ** 0.5


def gap_at(gx, gy, rv):
    worst = 9e9
    for (n, x, y, r, dr) in vias:
        if n == 'GND':
            d = ((gx - x) ** 2 + (gy - y) ** 2) ** 0.5 - dr - 0.1
            # hole-to-hole: new drill r = rv-0.1 approx; use drill 0.15
            d = ((gx - x) ** 2 + (gy - y) ** 2) ** 0.5 - dr - 0.15 - 0.2495
        else:
            d = ((gx - x) ** 2 + (gy - y) ** 2) ** 0.5 - r - rv - 0.2
        worst = min(worst, d)
    for (n, x, y, r, ref, num) in pads:
        if n == 'GND':
            continue
        d = ((gx - x) ** 2 + (gy - y) ** 2) ** 0.5 - r - rv - 0.2
        worst = min(worst, d)
    for (n, li, x1, y1, x2, y2, hw) in segs:
        if n == 'GND':
            continue
        d = segdist(gx, gy, x1, y1, x2, y2) - hw - rv - 0.2
        worst = min(worst, d)
    return worst


for ti in (9, 10, 14, 23):
    pts = polys[ti]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    print(f'--- island {ti} x[{min(xs):.2f},{max(xs):.2f}] '
          f'y[{min(ys):.2f},{max(ys):.2f}]', flush=True)
    contained = [(ref, num, n, round(x, 2), round(y, 2))
                 for (n, x, y, r, ref, num) in pads
                 if inside(pts, x, y)]
    print('   pads inside:', contained, flush=True)
    for rv, dn in ((0.30, 'd0.6'), (0.25, 'd0.5'), (0.225, 'd0.45'),
                   (0.20, 'd0.4')):
        best = None
        gx = min(xs)
        while gx <= max(xs):
            gy = min(ys)
            while gy <= max(ys):
                if inside(pts, gx, gy):
                    g = gap_at(gx, gy, rv)
                    if best is None or g > best[2]:
                        best = (gx, gy, g)
                gy += 0.05
            gx += 0.05
        print(f'   {dn}: best ({best[0]:.2f},{best[1]:.2f}) gap '
              f'{best[2]:+.3f}', flush=True)
print('T_AW27 COMPLETE', flush=True)
