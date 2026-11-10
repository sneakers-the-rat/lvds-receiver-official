import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp197.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
def track(netname, layer, w, pts):
    net = b.FindNet(netname)
    for a, bb in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
        t.SetWidth(M(w)); t.SetLayer(layer); t.SetNet(net); b.Add(t)
track('CF1', pcbnew.F_Cu, 0.2, [(67.5,39.9),(67.58,40.05)])
track('CF1', pcbnew.F_Cu, 0.15, [(67.58,40.05),(67.58,40.45)])
track('CF1', pcbnew.F_Cu, 0.2, [(67.58,40.45),(68.6,40.45),(68.6,42.05),(66.0,42.05),(66.0,41.55)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t23.kicad_pcb'); print('saved t23')
