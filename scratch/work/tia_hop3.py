import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp194.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
net = b.FindNet('TIA_OUT')
v = pcbnew.PCB_VIA(b)
v.SetPosition(pcbnew.VECTOR2I(M(20.95), M(42.5)))
v.SetDrill(M(0.3)); v.SetWidth(M(0.5))
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNet(net); b.Add(v)
pts = [(20.95,42.5), (21.3,41.2), (20.3,39.9), (18.9,40.635)]
for a, bb in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
    t.SetWidth(M(0.25)); t.SetLayer(pcbnew.In1_Cu); t.SetNet(net); b.Add(t)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t7.kicad_pcb'); print('saved t7')
