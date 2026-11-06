import pcbnew
b = pcbnew.LoadBoard('scratch/work/t_i2_base.kicad_pcb')
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

# DATP relay v2: F descent at x~65.96 to via (65.95,33.5) d0.6, B rejoin at staircase seg2 east end
track('CDR_DATP', pcbnew.F_Cu, 0.2, [(66.0,34.562),(65.96,34.0)])
via('CDR_DATP', 65.95, 33.5, d=0.6)
track('CDR_DATP', pcbnew.B_Cu, 0.2, [(65.95,33.5),(66.625,33.625)])
# DATN: via (66.51,34.05) east of DATP stub, F stub from U4.28 south edge, B run with north jog over DATP rejoin
track('CDR_DATN', pcbnew.F_Cu, 0.2, [(66.55,34.372),(66.51,34.05)])
via('CDR_DATN', 66.51, 34.05)
track('CDR_DATN', pcbnew.B_Cu, 0.3, [(66.51,34.05),(66.9,34.3),(79.625,31.75)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_i2.kicad_pcb'); print('saved t_i2')
