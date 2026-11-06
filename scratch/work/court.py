import pcbnew, sys
b=pcbnew.LoadBoard(sys.argv[1]); MM=pcbnew.ToMM
for fp in b.GetFootprints():
    if fp.GetReference() in ('C48','C19','X1','C23','R21','C49'):
        bb=fp.GetCourtyard(0) if hasattr(fp,'GetCourtyard') else None
        # courtyard via drawings on F.CrtYd
        pts=[]
        for d in fp.GraphicalItems():
            if d.GetLayer()==pcbnew.F_CrtYd:
                bbx=d.GetBoundingBox()
                pts.append((MM(bbx.GetLeft()),MM(bbx.GetTop()),MM(bbx.GetRight()),MM(bbx.GetBottom())))
        pos=fp.GetPosition()
        print(fp.GetReference(), 'at', round(MM(pos.x),2), round(MM(pos.y),2), 'crtyd boxes:', [(round(a,2),round(c,2),round(e,2),round(f,2)) for a,c,e,f in pts])
