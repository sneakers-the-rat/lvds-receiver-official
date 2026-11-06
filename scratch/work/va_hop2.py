import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp187.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
net = b.FindNet('+VA')
for (x, y) in [(37.725,39.975), (37.375,35.75)]:
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(M(x), M(y)))
    v.SetDrill(M(0.3)); v.SetWidth(M(0.5))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net); b.Add(v)
pts = [(37.725,39.975), (38.35,38.2), (38.35,36.9), (37.375,35.75)]
for a, bb in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
    t.SetWidth(M(0.3)); t.SetLayer(pcbnew.In1_Cu); t.SetNet(net); b.Add(t)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/s8.kicad_pcb'); print('saved s8')
