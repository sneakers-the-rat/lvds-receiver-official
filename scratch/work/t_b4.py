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

# SWCLK v4: F south, diagonal SW of R16.2 corner, via west, B south + east under J4 row into J4.4
track('SWCLK', pcbnew.F_Cu, 0.2, [(90.75,-17.0),(90.9,-18.1),(89.95,-18.75),(89.8,-19.3)])
via('SWCLK', 89.8, -19.3)
track('SWCLK', pcbnew.B_Cu, 0.2, [(89.8,-19.3),(89.8,-24.35),(92.52,-24.35),(92.52,-23.6)])
# DAC_VREF v4: stub NE + via clear of SDA via, In2 SW run, via west of +3V3A B vertical, F stub into C26.1
track('DAC_VREF', pcbnew.F_Cu, 0.2, [(70.7,5.25),(70.8,4.95)])
via('DAC_VREF', 70.8, 4.95)
track('DAC_VREF', pcbnew.In2_Cu, 0.2, [(70.8,4.95),(67.65,7.55)])
via('DAC_VREF', 67.65, 7.55)
track('DAC_VREF', pcbnew.F_Cu, 0.2, [(67.65,7.55),(68.6,8.6)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_b4.kicad_pcb'); print('saved t_b4')
