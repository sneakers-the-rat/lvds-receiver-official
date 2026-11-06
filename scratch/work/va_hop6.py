import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp191.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
net = b.FindNet('+VA')
v = pcbnew.PCB_VIA(b)
v.SetPosition(pcbnew.VECTOR2I(M(41.1), M(49.35)))
v.SetDrill(M(0.3)); v.SetWidth(M(0.5))
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNet(net); b.Add(v)
pts = [(41.1,49.35), (41.1,41.6), (38.6,41.6), (37.725,39.975)]
for a, bb in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
    t.SetWidth(M(0.3)); t.SetLayer(pcbnew.In1_Cu); t.SetNet(net); b.Add(t)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/s12.kicad_pcb'); print('saved s12')
