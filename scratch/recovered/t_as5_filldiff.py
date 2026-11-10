"""t_as5: compare filled-island structure of zones between two boards.
For each zone+layer: island count and total filled area (mm^2), plus the
bbox of every island, so a severed/new island can be located."""
import sys, wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
LAY = {pcbnew.F_Cu:'F', pcbnew.In1_Cu:'In1', pcbnew.In2_Cu:'In2', pcbnew.B_Cu:'B'}
def islands(path):
    b = pcbnew.LoadBoard(path)
    out = {}
    for z in b.Zones():
        net = z.GetNetname()
        for ln in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if not z.GetLayerSet().Contains(ln):
                continue
            ps = z.GetFilledPolygonsList(ln)
            n = ps.OutlineCount()
            tot = 0.0; boxes = []
            for i in range(n):
                o = ps.Outline(i)
                pts = [(MM(o.GetPoint(i).x), MM(o.GetPoint(i).y)) for i in range(o.PointCount())]
                # shoelace area
                ar = 0.0
                for j in range(len(pts)):
                    x1,y1 = pts[j]; x2,y2 = pts[(j+1) % len(pts)]
                    ar += x1*y2 - x2*y1
                tot += abs(ar)/2
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                boxes.append((round(min(xs),2), round(min(ys),2), round(max(xs),2), round(max(ys),2), round(abs(ar)/2,2)))
            out[(net, LAY[ln])] = (n, round(tot,2), boxes)
    return out
a = islands(sys.argv[1]); b = islands(sys.argv[2])
for k in sorted(set(a) | set(b)):
    if a.get(k, (0,0,[]))[:2] != b.get(k, (0,0,[]))[:2]:
        print(k, 'exp236:', a.get(k,(0,0))[:2], ' exp237:', b.get(k,(0,0))[:2])
        sa = set(a.get(k,(0,0,[]))[2]); sb = set(b.get(k,(0,0,[]))[2])
        for x in sorted(sb - sa): print('   NEW/CHANGED island:', x)
        for x in sorted(sa - sb): print('   LOST/CHANGED island:', x)
print('done')
