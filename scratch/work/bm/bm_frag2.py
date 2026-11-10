import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp266.kicad_pcb')
for z in b.Zones():
    if z.GetNetname() != 'GND' or z.GetLayer() != pcbnew.F_Cu:
        continue
    polys = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(polys.OutlineCount()):
        o = polys.Outline(i)
        xs = [o.GetPoint(j).x/1e6 for j in range(o.PointCount())]
        ys = [o.GetPoint(j).y/1e6 for j in range(o.PointCount())]
        if not (75.0 < min(xs) < 75.2 and 6.9 < min(ys) < 7.1):
            continue
        print('frag found, points:', o.PointCount())
        # scan grid for an interior point far from the boundary
        import math
        pts = list(zip(xs, ys))
        def dist_edge(px, py):
            d = 1e9
            for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
                vx, vy = bx-ax, by-ay
                t = max(0.0, min(1.0, ((px-ax)*vx + (py-ay)*vy) / (vx*vx + vy*vy + 1e-12)))
                d = min(d, math.hypot(px-(ax+t*vx), py-(ay+t*vy)))
            return d
        def inside(px, py):
            c = False
            for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
                if (ay > py) != (by > py) and px < (bx-ax) * (py-ay) / (by-ay) + ax:
                    c = not c
            return c
        best = None
        gx = 75.3
        while gx < 78.4:
            gy = 7.2
            while gy < 9.5:
                if inside(gx, gy):
                    d = dist_edge(gx, gy)
                    if best is None or d > best[0]:
                        best = (d, round(gx, 2), round(gy, 2))
                gy += 0.1
            gx += 0.1
        print('deepest interior point (dist, x, y):', best)
