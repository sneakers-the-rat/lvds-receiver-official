import pcbnew, math
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp184.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
targets = {'X2.2': (72.55,24.575), 'C16.2': (76.775,9.75), 'U6.51': (80.25,4.662), 'U6.38': (73.75,4.662)}
def inpoly(x, y, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x1,y1 = pts[i]; x2,y2 = pts[(i+1)%n]
        if (y1 > y) != (y2 > y):
            if x < (x2-x1)*(y-y1)/(y2-y1)+x1: inside = not inside
    return inside
outlines = []
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu): continue
    ps = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
        outlines.append((i, pts))
for name,(tx,ty) in targets.items():
    hits = [i for i,pts in outlines if inpoly(tx,ty,pts)]
    print(name, 'inside outlines', hits)
# for each island outline, closest vertex distance to main outline (0) boundary segments
def segdist(p, a, b):
    ax,ay = a; bx,by = b; px,py = p
    dx,dy = bx-ax, by-ay
    L2 = dx*dx+dy*dy
    t = 0 if L2==0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))
main = outlines[0][1]
mainsegs = [(main[i], main[(i+1)%len(main)]) for i in range(len(main))]
for idx, pts in outlines:
    if idx == 0: continue
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    contains = [n for n,(tx,ty) in targets.items() if inpoly(tx,ty,pts)]
    if not contains: continue
    best = (1e9, None)
    for p in pts:
        for a,bb in mainsegs:
            d = segdist(p, a, bb)
            if d < best[0]: best = (d, p)
    print(f'island outline {idx} {contains}: closest vertex to main fill {best[0]:.3f} mm at {best[1]}')
