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

# DP_CON: grid_route B geometry (saved GND-mislabeled there; re-emitted as DP_CON),
# end adjusted to via (29.9,72.3) in the J1 inter-row channel; F stubs into A6 and B6.
track('DP_CON', pcbnew.B_Cu, 0.25, [(43.75,47.625),(41.375,57.375),(32.25,70.875),(31.875,71.25),(30.25,71.625),(29.9,72.3)])
via('DP_CON', 43.75, 47.625)
track('DP_CON', pcbnew.F_Cu, 0.2, [(43.75,47.625),(44.362,47.3)])
via('DP_CON', 29.9, 72.3)
track('DP_CON', pcbnew.F_Cu, 0.2, [(29.9,72.3),(29.75,71.7)])
track('DP_CON', pcbnew.F_Cu, 0.2, [(29.9,72.3),(30.0,72.95)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_f3.kicad_pcb'); print('saved t_f3')
