import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp197.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
def track(netname, layer, w, pts):
    net = b.FindNet(netname)
    for a, bb in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
        t.SetWidth(M(w)); t.SetLayer(layer); t.SetNet(net); b.Add(t)
def via(netname, x, y, dia=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(M(x), M(y)))
    v.SetDrill(M(drill)); v.SetWidth(M(dia))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet(netname)); b.Add(v)
track('CF1', pcbnew.F_Cu, 0.2, [(67.5,39.95),(67.6,40.1)])
track('CF1', pcbnew.F_Cu, 0.15, [(67.6,40.1),(67.6,40.45)])
track('CF1', pcbnew.F_Cu, 0.2, [(67.6,40.45),(68.6,40.45),(68.6,42.05),(66.0,42.05),(66.0,41.55)])
track('CDR_NIN', pcbnew.F_Cu, 0.2, [(63.55,37.0),(63.3,36.3),(62.95,35.85),(60.0,36.35),(58.4,36.35),(57.8,35.6),(54.2,35.4),(54.2,36.9)])
via('CDR_NIN', 54.2, 36.9)
track('CDR_NIN', pcbnew.B_Cu, 0.2, [(54.2,36.9),(54.2,38.6)])
via('CDR_NIN', 54.2, 38.6)
track('CDR_NIN', pcbnew.F_Cu, 0.2, [(54.2,38.6),(54.2,44.3),(51.3,44.5),(50.9,45.2)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t22.kicad_pcb'); print('saved t22')
