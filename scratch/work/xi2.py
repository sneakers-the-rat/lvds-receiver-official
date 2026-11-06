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
track('XI', pcbnew.F_Cu, 0.2, [(76.25,11.2),(76.6,10.6),(76.95,10.45)])
via('XI', 76.95, 10.45)
track('XI', pcbnew.B_Cu, 0.25, [(76.95,10.45),(76.95,16.75),(72.7,16.75),(72.5,16.6)])
via('XI', 72.5, 16.6)
track('XI', pcbnew.F_Cu, 0.2, [(72.5,16.6),(72.5,18.95)])
via('XI', 72.5, 18.95)
track('XI', pcbnew.B_Cu, 0.2, [(72.5,18.95),(73.8,18.2),(75.8,18.75)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t14.kicad_pcb'); print('saved t14')
