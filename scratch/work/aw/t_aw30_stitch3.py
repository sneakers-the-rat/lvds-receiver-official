"""t_aw30: fast stitch-point search for orphan GND islands 10, 14, 23.
Obstacles prefiltered to the island bbox + 1.5 mm; coarse grid 0.1
then refine 0.025. Gap = worst over foreign vias/pads/segs of
(dist - r_item - r_via - 0.2) and hole spacing vs GND vias."""
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


vias = []
pads = []
segs = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition())
        vias.append((t.GetNetname(), p[0], p[1],
                     pcbnew.ToMM(t.GetWidth()) / 2,
                     pcbnew.ToMM(t.GetDrill()) / 2))
    else:
        a = pcbnew.ToMM(t.GetStart())
        c = pcbnew.ToMM(t.GetEnd())
        segs.append((t.GetNetname(), a[0], a[1], c[0], c[1],
                     pcbnew.ToMM(t.GetWidth()) / 2))
for fp in b.GetFootprints():
    for p in fp.Pads():
        pp = pcbnew.ToMM(p.GetPosition())
        sz = pcbnew.ToMM(p.GetSize())
        pads.append((p.GetNetname(), pp[0], pp[1], max(sz) / 2,
                     fp.GetReference(), p.GetNumber()))


def segdist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    tt = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return ((px - x1 - tt * dx) ** 2 + (py - y1 - tt * dy) ** 2) ** 0.5


for ti in (10, 14, 23):
    pts = polys[ti]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    print(f'--- island {ti} x[{x0:.2f},{x1:.2f}] y[{y0:.2f},{y1:.2f}]',
          flush=True)
    contained = [(ref, num, round(x, 2), round(y, 2))
                 for (n, x, y, r, ref, num) in pads
                 if n == 'GND' and inside(pts, x, y)]
    print('   GND pads inside:', contained, flush=True)
    M = 1.5
    ov = [v for v in vias if x0 - M < v[1] < x1 + M
          and y0 - M < v[2] < y1 + M]
    op = [p for p in pads if x0 - M < p[1] < x1 + M
          and y0 - M < p[2] < y1 + M]
    os_ = [s for s in segs
           if not (max(s[1], s[3]) < x0 - M or min(s[1], s[3]) > x1 + M
                   or max(s[2], s[4]) < y0 - M
                   or min(s[2], s[4]) > y1 + M)]

    def gap_at(gx, gy, rv):
        worst = 9e9
        for (n, x, y, r, dr) in ov:
            dd = ((gx - x) ** 2 + (gy - y) ** 2) ** 0.5
            if n == 'GND':
                d = dd - dr - 0.15 - 0.2495
            else:
                d = dd - r - rv - 0.2
            if d < worst:
                worst = d
        for (n, x, y, r, ref, num) in op:
            if n == 'GND':
                continue
            d = ((gx - x) ** 2 + (gy - y) ** 2) ** 0.5 - r - rv - 0.2
            if d < worst:
                worst = d
        for (n, sx1, sy1, sx2, sy2, hw) in os_:
            if n == 'GND':
                continue
            d = segdist(gx, gy, sx1, sy1, sx2, sy2) - hw - rv - 0.2
            if d < worst:
                worst = d
        return worst

    for rv, dn in ((0.30, 'd0.6'), (0.25, 'd0.5'), (0.225, 'd0.45'),
                   (0.20, 'd0.4')):
        best = None
        gx = x0
        while gx <= x1:
            gy = y0
            while gy <= y1:
                if inside(pts, gx, gy):
                    gv = gap_at(gx, gy, rv)
                    if best is None or gv > best[2]:
                        best = (gx, gy, gv)
                gy += 0.1
            gx += 0.1
        # refine
        bx, by, bg = best
        gx = bx - 0.1
        while gx <= bx + 0.1:
            gy = by - 0.1
            while gy <= by + 0.1:
                if inside(pts, gx, gy):
                    gv = gap_at(gx, gy, rv)
                    if gv > bg:
                        bx, by, bg = gx, gy, gv
                gy += 0.025
            gx += 0.025
        print(f'   {dn}: best ({bx:.3f},{by:.3f}) gap {bg:+.3f}',
              flush=True)
print('T_AW30 COMPLETE', flush=True)
