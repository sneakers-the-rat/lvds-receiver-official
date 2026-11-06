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

# SWCLK v2: F east along U6 south face, via, B around the east end of J4, west under the header row, north into J4.4
track('SWCLK', pcbnew.F_Cu, 0.2, [(90.75,-16.663),(92.3,-16.663),(92.3,-16.9)])
via('SWCLK', 92.3, -16.9)
track('SWCLK', pcbnew.B_Cu, 0.2, [(92.3,-16.9),(93.6,-18.5),(97.85,-20.5),(97.85,-24.35),(92.52,-24.35),(92.52,-23.6)])
# DAC_VREF v2: via on U8.10 pad SE corner, In2 SW run, via, F stub into C26.1
via('DAC_VREF', 71.45, 5.1)
track('DAC_VREF', pcbnew.In2_Cu, 0.2, [(71.45,5.1),(68.15,7.9)])
via('DAC_VREF', 68.15, 7.9)
track('DAC_VREF', pcbnew.F_Cu, 0.2, [(68.15,7.9),(68.7,8.62)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_b2.kicad_pcb'); print('saved t_b2')
