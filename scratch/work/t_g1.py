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

# +3V3D U11.14: grid_route In2 run to C38.1; via north of U11 row + F stub into U11.14; via at path end
track('+3V3D', pcbnew.In2_Cu, 0.6, [(56.875,24.375),(64.625,20.75),(65.25,20.75),(65.875,21.375),(66.125,22.0)])
via('+3V3D', 56.75, 23.9)
track('+3V3D', pcbnew.In2_Cu, 0.2, [(56.75,23.9),(56.875,24.375)])
track('+3V3D', pcbnew.F_Cu, 0.2, [(56.75,23.9),(56.75,24.6)])
via('+3V3D', 66.125, 22.0)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_g1.kicad_pcb'); print('saved t_g1')
