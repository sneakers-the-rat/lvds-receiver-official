import sys, pcbnew
# usage: place_tracks.py IN OUT NET LAYER WIDTH x1 y1 x2 y2 [x3 y3 ...] (polyline pts)
src, dst, netname, layername, width = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
pts = [(float(sys.argv[i]), float(sys.argv[i+1])) for i in range(6, len(sys.argv), 2)]
b = pcbnew.LoadBoard(src)
def M(x): return pcbnew.FromMM(x)
LAYER = {'F': pcbnew.F_Cu, 'In1': pcbnew.In1_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}[layername]
net = b.FindNet(netname)
for a, bb in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
    t.SetWidth(M(width)); t.SetLayer(LAYER); t.SetNet(net)
    b.Add(t)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save(dst); print('saved', dst)
