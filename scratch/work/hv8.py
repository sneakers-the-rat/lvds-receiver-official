import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp196.kicad_pcb')
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
track('HV_VC', pcbnew.F_Cu, 0.2, [(21.925,-3.0),(21.3,-3.6),(22.2,-4.6),(23.5,-4.55),(24.85,-4.08)])
via('HV_VC2', 20.725, -1.5)
track('HV_VC2', pcbnew.B_Cu, 0.2, [(20.725,-1.5),(23.45,-3.15)])
via('HV_VC2', 23.45, -3.15)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t20.kicad_pcb'); print('saved t20')
