import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp184.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
def inpoly(x, y, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x1,y1 = pts[i]; x2,y2 = pts[(i+1)%n]
        if (y1 > y) != (y2 > y):
            if x < (x2-x1)*(y-y1)/(y2-y1)+x1: inside = not inside
    return inside
out = {}
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu): continue
    ps = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        out[i] = [(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
for name,(tx,ty) in {'C46.2': (68.775,24.5), 'C38.2': (68.45,22.75), 'R17.2': (70.825,21.0), 'C28.2': (74.275,20.5)}.items():
    print(name, 'in outlines', [i for i,p in out.items() if inpoly(tx,ty,p)])
print('outline6 boundary points x 72.8..74.2, y 20..25:')
pts = out[6]
for i,(x,y) in enumerate(pts):
    if 72.8 <= x <= 74.2 and 20 <= y <= 25:
        print(f'  ({x:.3f},{y:.3f})')
print('outline7 boundary points x 72.8..74.2, y 20..25:')
pts = out[7]
for i,(x,y) in enumerate(pts):
    if 72.8 <= x <= 74.2 and 20 <= y <= 25:
        print(f'  ({x:.3f},{y:.3f})')
# scanline: for x in 73.3..73.9 step .05, find outline6 fill y-intervals in 20..26 and outline7 intervals
for x in (73.3, 73.45, 73.6, 73.75, 73.9):
    row = []
    for oi in (6,7):
        pts = out[oi]
        ys = []
        n = len(pts)
        for i in range(n):
            x1,y1 = pts[i]; x2,y2 = pts[(i+1)%n]
            if (x1 > x) != (x2 > x):
                ys.append((y2-y1)*(x-x1)/(x2-x1)+y1)
        ys.sort()
        row.append((oi, [round(v,2) for v in ys if 19 < v < 27]))
    print('x=', x, row)
