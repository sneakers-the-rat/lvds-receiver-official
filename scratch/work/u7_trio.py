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
# USB_RST pure F
track('USB_RST', pcbnew.F_Cu, 0.2, [(74.25,16.438),(73.95,16.438),(74.45,15.4),(74.45,8.9),(73.85,8.3),(73.85,6.9),(74.45,6.3),(74.45,5.75),(74.72,5.35),(74.75,4.95)])
# XI: F stub + via + B north
track('XI', pcbnew.F_Cu, 0.2, [(76.25,11.35),(76.3,11.0)])
via('XI', 76.3, 11.0)
track('XI', pcbnew.B_Cu, 0.2, [(76.3,11.0),(76.25,18.8),(75.8,18.8)])
# XO: F stub + via + B west + via + In2 stub
track('XO', pcbnew.F_Cu, 0.2, [(76.75,11.35),(76.75,10.75)])
via('XO', 76.75, 10.75)
track('XO', pcbnew.B_Cu, 0.25, [(76.75,10.75),(76.75,12.3),(74.75,12.3),(74.35,12.9),(72.65,13.0)])
via('XO', 72.65, 13.0)
track('XO', pcbnew.In2_Cu, 0.25, [(72.65,13.0),(73.15,13.0)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t12.kicad_pcb'); print('saved t12')
