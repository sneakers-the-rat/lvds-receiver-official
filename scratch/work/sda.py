import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp198.kicad_pcb')
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
track('I2C_SDA', pcbnew.F_Cu, 0.2, [(68.8,37.1),(69.45,36.95),(69.45,34.3)])
via('I2C_SDA', 69.45, 34.3)
track('I2C_SDA', pcbnew.B_Cu, 0.2, [(69.45,34.3),(69.45,0.625),(69.75,0.625)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t27.kicad_pcb'); print('saved t27')
