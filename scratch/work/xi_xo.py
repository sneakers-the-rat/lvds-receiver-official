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
# XO pure F west
track('XO', pcbnew.F_Cu, 0.2, [(76.75,11.35),(76.75,10.7),(72.55,10.7),(72.55,9.9),(72.1,9.9)])
# XI via + B north/west + via + F hop + via + B east
track('XI', pcbnew.F_Cu, 0.2, [(76.25,11.35),(76.35,11.05)])
via('XI', 76.35, 11.05)
track('XI', pcbnew.B_Cu, 0.25, [(76.35,11.05),(76.25,16.75),(72.7,16.75),(72.5,16.6)])
via('XI', 72.5, 16.6)
track('XI', pcbnew.F_Cu, 0.2, [(72.5,16.6),(72.5,18.3)])
via('XI', 72.5, 18.3)
track('XI', pcbnew.B_Cu, 0.2, [(72.5,18.3),(75.8,18.8)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t13.kicad_pcb'); print('saved t13')
