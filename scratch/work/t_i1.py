import pcbnew
b = pcbnew.LoadBoard('scratch/work/t_i1_base.kicad_pcb')
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

# DATP relay: F exit west-down to via (65.5,33.75), B rejoin to staircase start (66.375,33.875)
track('CDR_DATP', pcbnew.F_Cu, 0.2, [(66.0,34.562),(65.98,34.372),(65.65,33.85)])
via('CDR_DATP', 65.5, 33.75, d=0.6)
track('CDR_DATP', pcbnew.B_Cu, 0.2, [(65.5,33.75),(66.375,33.875)])
# DATN: via overlapping U4.28 west strip at (66.42,34.55) + grid B run to R13 tree
via('CDR_DATN', 66.42, 34.55)
track('CDR_DATN', pcbnew.B_Cu, 0.3, [(66.42,34.55),(79.625,31.75)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_i1.kicad_pcb'); print('saved t_i1')
