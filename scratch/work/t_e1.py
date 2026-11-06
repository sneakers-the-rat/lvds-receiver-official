import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp200.kicad_pcb')
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

# APD_K: In2 run (grid_route segment) + via into C33.1 pad edge + via at D1.5 pad NE corner
track('APD_K', pcbnew.In2_Cu, 0.4, [(10.5,29.375),(9.5,39.75)])
via('APD_K', 10.5, 29.375)
via('APD_K', 9.5, 39.75)
# APD_A: jog from y38.375 web south into D1.6; bridge D1.3 pad east edge -> D1.4 along y41.1
track('APD_A', pcbnew.F_Cu, 0.2, [(9.0,38.375),(9.0,38.9)])
track('APD_A', pcbnew.F_Cu, 0.2, [(7.8,41.1),(8.85,41.1)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_e1.kicad_pcb'); print('saved t_e1')
