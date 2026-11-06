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

# ULPI_D2: F jog east from U7.22 (D4 pattern), via (79.375,13.25), grid_route In2 segments,
# via (78.25,6.6) north of U6 row, F jog south into U6.47
track('ULPI_D2', pcbnew.F_Cu, 0.2, [(78.438,13.25),(79.375,13.25)])
via('ULPI_D2', 79.375, 13.25)
track('ULPI_D2', pcbnew.In2_Cu, 0.25, [(79.375,13.25),(78.125,13.125),(77.0,10.375),(78.125,5.375),(78.25,6.6)])
via('ULPI_D2', 78.25, 6.6)
track('ULPI_D2', pcbnew.F_Cu, 0.2, [(78.25,6.6),(78.25,5.0)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_f2.kicad_pcb'); print('saved t_f2')
