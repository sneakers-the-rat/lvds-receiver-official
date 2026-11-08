"""t_as6: print outline points of the F GND island whose bbox matches
x[73.0,74.0] y[2.4,5.6] in exp237, and test candidate via points for
in-polygon (ray cast) + all-layer model margin as GND."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, fmt_it
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp237.kicad_pcb')
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.GetLayerSet().Contains(pcbnew.F_Cu):
        continue
    ps = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [(MM(o.GetPoint(j).x), MM(o.GetPoint(j).y)) for j in range(o.PointCount())]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if min(xs) > 72.9 and max(xs) < 74.1 and min(ys) > 2.3 and max(ys) < 5.7:
            print('ISLAND outline:')
            for p in pts: print(f'   ({p[0]:.3f},{p[1]:.3f})')
            # candidate points: grid inside bbox, ray-cast test
            def inside(x, y):
                c = False
                for j in range(len(pts)):
                    x1,y1 = pts[j]; x2,y2 = pts[(j+1) % len(pts)]
                    if (y1 > y) != (y2 > y):
                        if x < (x2-x1)*(y-y1)/(y2-y1)+x1: c = not c
                return c
            items = load_items(b)
            print('candidate via points (in-fill, margin>=0 all layers):')
            gx = 73.15
            while gx <= 73.95:
                gy = 2.6
                while gy <= 5.5:
                    if inside(gx, gy):
                        worst = 9
                        for l in range(3):
                            m,w = pt_margin(l, gx, gy, 'GND', 0.25, list(items[l]))
                            if m < worst: worst = m
                        if worst >= 0:
                            print(f'   ({gx:.2f},{gy:.2f}) worst {worst:+.3f}')
                    gy += 0.05
                gx += 0.05
print('done')
