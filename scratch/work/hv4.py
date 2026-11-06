import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp196.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
def track(netname, layer, w, pts):
    net = b.FindNet(netname)
    for a, bb in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
        t.SetWidth(M(w)); t.SetLayer(layer); t.SetNet(net); b.Add(t)
track('HV_VC', pcbnew.F_Cu, 0.2, [(21.925,-3.0),(21.3,-3.6),(22.2,-4.6),(23.5,-4.55),(24.85,-4.08)])
track('HV_VC2', pcbnew.F_Cu, 0.2, [(21.05,-1.85),(22.15,-2.55),(23.4,-2.85)])
track('HV_INTVCC', pcbnew.F_Cu, 0.2, [(31.225,-0.9),(31.0,-2.2),(30.2,-2.95)])
track('HV_GATE', pcbnew.F_Cu, 0.2, [(23.925,-8.75),(23.3,-9.6),(25.0,-10.3),(27.5,-9.9)])
track('HV_GATE', pcbnew.F_Cu, 0.15, [(27.5,-9.9),(28.64,-7.6),(28.64,-2.5)])
track('HV_GATE', pcbnew.F_Cu, 0.2, [(28.64,-2.5),(29.3,-2.5)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t15.kicad_pcb'); print('saved t15')
