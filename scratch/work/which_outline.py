import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp186.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
def inpoly(x, y, pts):
    inside = False; n = len(pts)
    for i in range(n):
        x1,y1 = pts[i]; x2,y2 = pts[(i+1)%n]
        if (y1 > y) != (y2 > y):
            if x < (x2-x1)*(y-y1)/(y2-y1)+x1: inside = not inside
    return inside
targets = {'U6.51': (80.25,4.662), 'U6.38': (73.75,4.662), 'U6.61': (85.25,4.662)}
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu): continue
    ps = z.GetFilledPolysList(pcbnew.F_Cu)
    print('F GND outlines:', ps.OutlineCount())
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        hits = [k for k,(tx,ty) in targets.items() if inpoly(tx,ty,pts)]
        print(f'  outline {i}: area~{o.Area():.3g} bbox x {min(xs):.2f}..{max(xs):.2f} y {min(ys):.2f}..{max(ys):.2f} holds {hits}')
