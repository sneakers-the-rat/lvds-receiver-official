"""t_aw26: empirical GND stitch test. Copy exp241, add d0.6 GND vias at
max-clearance interior points of the split-suspect F islands, refill,
save test board. DRC arbitrates."""
import wx
_app = wx.App(False)
import pcbnew
import sys

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


# foreign + GND-via obstacle list (centre, radius) on all layers for vias,
# F only matters for the via disc vs tracks: use all-layer items.
obs = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition())
        obs.append(('via', t.GetNetname(), p[0], p[1],
                    pcbnew.ToMM(t.GetWidth()) / 2))
for fp in b.GetFootprints():
    for p in fp.Pads():
        pp = pcbnew.ToMM(p.GetPosition())
        sz = pcbnew.ToMM(p.GetSize())
        obs.append(('pad', p.GetNetname(), pp[0], pp[1],
                    max(sz[0], sz[1]) / 2))
segs = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    a = pcbnew.ToMM(t.GetStart())
    c = pcbnew.ToMM(t.GetEnd())
    segs.append((t.GetNetname(), t.GetLayer(), a[0], a[1], c[0], c[1],
                 pcbnew.ToMM(t.GetWidth()) / 2))


def segdist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    tt = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return ((px - x1 - tt * dx) ** 2 + (py - y1 - tt * dy) ** 2) ** 0.5


LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
targets = [int(x) for x in sys.argv[1].split(',')]
nc_gnd = b.GetNetcodeFromNetname('GND')
placed = []
for ti in targets:
    pts = polys[ti]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    best = None
    gx = min(xs)
    while gx <= max(xs):
        gy = min(ys)
        while gy <= max(ys):
            if inside(pts, gx, gy):
                mind = 9e9
                for (k, n, ox, oy, r) in obs:
                    if n == 'GND' and k == 'pad':
                        continue
                    d = ((gx - ox) ** 2 + (gy - oy) ** 2) ** 0.5 - r
                    if n == 'GND' and k == 'via':
                        d = ((gx - ox) ** 2 + (gy - oy) ** 2) ** 0.5
                        d = d - 0.3  # hole spacing vs GND via drill/2..
                    mind = min(mind, d)
                for (n, l, x1, y1, x2, y2, hw) in segs:
                    if n == 'GND':
                        continue
                    d = segdist(gx, gy, x1, y1, x2, y2) - hw
                    mind = min(mind, d)
                if best is None or mind > best[2]:
                    best = (gx, gy, mind)
            gy += 0.25
        gx += 0.25
    print(f'island {ti}: best stitch ({best[0]:.2f},{best[1]:.2f}) '
          f'min-obstacle-dist {best[2]:.3f}', flush=True)
    if best[2] < 0.5:
        print(f'  WARNING: tight stitch on island {ti}', flush=True)
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(best[0]),
                                  pcbnew.FromMM(best[1])))
    v.SetWidth(pcbnew.FromMM(0.6))
    v.SetDrill(pcbnew.FromMM(0.3))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(nc_gnd)
    b.Add(v)
    placed.append((best[0], best[1]))

from pcbnew import ZONE_FILLER
filler = ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp241stitch.kicad_pcb')
print('placed:', placed, flush=True)
print('T_AW26 COMPLETE', flush=True)
