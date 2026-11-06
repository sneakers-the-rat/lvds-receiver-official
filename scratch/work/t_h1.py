import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp201.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
def track(netname, layer, w, pts):
    net = b.FindNet(netname)
    for a, bb in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
        t.SetWidth(M(w)); t.SetLayer(layer); t.SetNet(net); b.Add(t)
def via(netname, x, y, d=0.5, drill=0.3):
    net = b.FindNet(netname)
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(M(x), M(y)))
    v.SetDrill(M(drill)); v.SetWidth(M(d))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net); b.Add(v)

# SLICEN v3: grid In2 path; U4-end via south of the row at (63.05,39.6) via F west+south stub;
# C13-end via (61.6,37.03) overlapping C13.2 pad west strip, on the In2 path.
track('SLICEN', pcbnew.In2_Cu, 0.25, [(63.375,38.625),(60.875,39.75),(60.5,39.625),(60.0,39.125),(60.125,38.5),(60.625,38.0),(61.75,37.0),(61.875,37.0)])
track('SLICEN', pcbnew.F_Cu, 0.2, [(63.372,38.5),(63.05,38.5),(63.05,39.6)])
via('SLICEN', 63.05, 39.6)
track('SLICEN', pcbnew.In2_Cu, 0.2, [(63.05,39.6),(63.2,38.8)])
via('SLICEN', 61.6, 37.03)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_h1.kicad_pcb'); print('saved t_h1')
