import pcbnew, math
exec(open('scratch/work/viascan.py').read().split("targets =")[0])  # reuse copper model + via_legal + board b
def inpoly(x, y, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x1,y1 = pts[i]; x2,y2 = pts[(i+1)%n]
        if (y1 > y) != (y2 > y):
            if x < (x2-x1)*(y-y1)/(y2-y1)+x1: inside = not inside
    return inside
def mm(v): return pcbnew.ToMM(v)
poly10 = None
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu): continue
    ps = z.GetFilledPolysList(pcbnew.F_Cu)
    o = ps.Outline(10)
    poly10 = [(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
hits = []
x = 74.9
while x <= 77.8:
    y = 7.0
    while y <= 10.9:
        if inpoly(round(x,3), round(y,3), poly10) and not via_legal(round(x,3), round(y,3)):
            hits.append((round(x,2), round(y,2)))
        y += 0.125
    x += 0.125
print('C16 island interior legal via spots:', hits if hits else 'NONE')
