import pcbnew, sys
SRC=sys.argv[1]
b=pcbnew.LoadBoard(SRC)
MM=pcbnew.ToMM
def pip(x,y,pts):
    inside=False; n=len(pts)
    for i in range(n):
        x1,y1=pts[i]; x2,y2=pts[(i+1)%n]
        if (y1>y)!=(y2>y):
            xin=x1+(y-y1)*(x2-x1)/(y2-y1)
            if x<xin: inside=not inside
    return inside
for z in b.Zones():
    if z.GetNetname()!='GND' or z.GetLayer()!=pcbnew.F_Cu: continue
    polys=z.GetFilledPolysList(pcbnew.F_Cu)
    print(f"F GND zone: {polys.OutlineCount()} filled outlines")
    pads=[]
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname()=='GND':
                p=pad.GetPosition(); pads.append((fp.GetReference()+'.'+pad.GetNumber(), MM(p.x), MM(p.y)))
    vias=[]
    for t in b.GetTracks():
        if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=='GND':
            p=t.GetPosition(); vias.append((MM(p.x),MM(p.y)))
    for i in range(polys.OutlineCount()):
        o=polys.Outline(i)
        pts=[(MM(o.CPoint(k).x),MM(o.CPoint(k).y)) for k in range(o.PointCount())]
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        area=o.Area()/1e12
        inside_p=[n for n,x,y in pads if pip(x,y,pts)]
        inside_v=[(round(x,2),round(y,2)) for x,y in vias if pip(x,y,pts)]
        print(f" island {i}: area={area:.2f} bbox=({min(xs):.1f},{min(ys):.1f})-({max(xs):.1f},{max(ys):.1f}) pads={inside_p} vias={inside_v}")
