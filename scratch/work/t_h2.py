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

# HV_GATE v4: grid B path + R27 via + F diagonal NE to via (31.75,-1.6) + B stub to path end
track('HV_GATE', pcbnew.B_Cu, 0.25, [(24.375,-8.375),(27.375,-6.875),(27.875,-6.25),(28.0,-4.75),(27.5,-2.875),(29.375,0.125),(29.875,0.25),(30.375,-0.125),(30.5,-1.0),(30.375,-2.375)])
via('HV_GATE', 24.375, -8.375)
track('HV_GATE', pcbnew.F_Cu, 0.15, [(30.375,-2.5),(31.6,-1.55)])
via('HV_GATE', 31.7, -1.5)
track('HV_GATE', pcbnew.B_Cu, 0.2, [(31.6,-1.55),(30.375,-2.375)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_h2.kicad_pcb'); print('saved t_h2')
