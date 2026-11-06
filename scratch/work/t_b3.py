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

# SWCLK v3: d0.45 via in U6.109 pad (exact-fit channel), B south weave crossing
# NRST's vertical north of its end, around J4 east end, west under header, into J4.4
track('SWCLK', pcbnew.F_Cu, 0.2, [(90.75,-16.663),(90.825,-16.85)])
via('SWCLK', 90.825, -16.85, d=0.45, drill=0.25)
track('SWCLK', pcbnew.B_Cu, 0.2, [(90.825,-16.85),(90.6,-18.6),(93.6,-19.3),(96.5,-18.5),(97.85,-18.3),(97.85,-24.35),(92.52,-24.35),(92.52,-23.6)])
# DAC_VREF v3: F stub + via east of U8.10, In2 SW run, via west clear of +3V3A B, F stub into C26.1
track('DAC_VREF', pcbnew.F_Cu, 0.2, [(70.9,5.25),(71.68,5.2)])
via('DAC_VREF', 71.68, 5.2)
track('DAC_VREF', pcbnew.In2_Cu, 0.2, [(71.68,5.2),(67.9,7.7)])
via('DAC_VREF', 67.9, 7.7)
track('DAC_VREF', pcbnew.F_Cu, 0.2, [(67.9,7.7),(68.6,8.6)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_b3.kicad_pcb'); print('saved t_b3')
