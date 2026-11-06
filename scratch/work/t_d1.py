import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp199.kicad_pcb')
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

# DAC_VREF: grid_route In2 segment (from gr_dac_In2 trial) + via pair
track('DAC_VREF', pcbnew.In2_Cu, 0.25, [(70.0,5.375),(69.51,7.85)])
via('DAC_VREF', 70.3, 5.0)                      # overlaps U8.10 pad edge (contact), clears +3V3D F y5.75 track + U8.9
track('DAC_VREF', pcbnew.In2_Cu, 0.2, [(70.3,5.0),(70.0,5.375)])
via('DAC_VREF', 69.51, 7.85)                    # on the In2 segment; clears +3V3A B y8.62 track
track('DAC_VREF', pcbnew.F_Cu, 0.2, [(69.51,7.85),(69.3,8.7)])   # into C26.1 pad
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_d1.kicad_pcb'); print('saved t_d1')
