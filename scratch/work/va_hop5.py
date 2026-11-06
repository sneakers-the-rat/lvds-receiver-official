import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp190.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
net = b.FindNet('+VA')
v = pcbnew.PCB_VIA(b)
v.SetPosition(pcbnew.VECTOR2I(M(15.025), M(50.5)))
v.SetDrill(M(0.3)); v.SetWidth(M(0.5))
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNet(net); b.Add(v)
pts = [(15.025,50.5), (15.8,42.0), (18.5,39.365)]
for a, bb in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
    t.SetWidth(M(0.3)); t.SetLayer(pcbnew.In1_Cu); t.SetNet(net); b.Add(t)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/s11.kicad_pcb'); print('saved s11')
