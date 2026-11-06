import pcbnew, math, sys
mm = lambda v: v/1e6
b = pcbnew.LoadBoard('scratch/stitch182c.kicad_pcb')
LN = {pcbnew.F_Cu:'F', pcbnew.In1_Cu:'In1', pcbnew.In2_Cu:'In2', pcbnew.B_Cu:'B'}
polys_by_layer = {}
for z in b.Zones():
    if z.GetNetname() != 'GND': continue
    for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        if not z.IsOnLayer(l): continue
        polys = z.GetFilledPolysList(l)
        lst = []
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            lst.append([(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())])
        polys_by_layer.setdefault(l, []).extend(lst)
def in_poly(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % len(poly)]
        if (y1 > y) != (y2 > y):
            if x < (x2-x1)*(y-y1)/(y2-y1)+x1: inside = not inside
    return inside
def pt_poly_dist(x, y, poly):
    d = 1e9
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % len(poly)]
        px, py = x-x1, y-y1; dx, dy = x2-x1, y2-y1
        L2 = dx*dx+dy*dy; t = 0.0 if L2 == 0 else max(0.0, min(1.0, (px*dx+py*dy)/L2))
        d = min(d, math.hypot(px-t*dx, py-t*dy))
    return d
for (qx, qy, name) in [(26.58, -2.0, 'U10.5 via'), (23.22, -1.5, 'C29.2 stub end'), (25.35, -2.0, 'U10.5 pad'), (22.27, -1.5, 'C29.2 pad')]:
    print(f'--- {name} ({qx},{qy})')
    for l, polys in polys_by_layer.items():
        inside = any(in_poly(qx, qy, p) for p in polys)
        d = min((pt_poly_dist(qx, qy, p) for p in polys), default=99)
        print(f'   {LN[l]}: inside={inside} nearest fill edge {0.0 if inside else round(d,2)} mm')
