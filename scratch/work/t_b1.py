import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp198.kicad_pcb')
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

# SWCLK: F south-west weave, via, B east into J4.4 (PTH)
track('SWCLK', pcbnew.F_Cu, 0.2, [(90.75,-17.0),(90.75,-18.2),(89.9,-19.6),(89.9,-24.35)])
via('SWCLK', 89.9, -24.35)
track('SWCLK', pcbnew.B_Cu, 0.2, [(89.9,-24.35),(92.52,-24.35),(92.52,-23.6)])
# SET_P: straight east run U13.7 -> R40.1
track('SET_P', pcbnew.F_Cu, 0.2, [(41.3,50.75),(43.1,50.75)])
# DAC_VREF: U8.10 east, south, west over C26.2, south into C26.1
track('DAC_VREF', pcbnew.F_Cu, 0.2, [(70.7,5.25),(71.75,5.25),(71.75,8.2),(68.975,8.2),(68.975,8.7)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_b1.kicad_pcb'); print('saved t_b1')
