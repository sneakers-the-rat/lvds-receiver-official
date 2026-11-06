import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp196.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
net = b.FindNet('+3V3A')
pts = [(73.9,14.75), (72.9,14.75), (72.45,13.95), (69.05,13.95), (69.05,15.6), (68.6,15.6), (68.6,18.0), (68.3,18.0)]
for a, bb in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
    t.SetWidth(M(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net); b.Add(t)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t11.kicad_pcb'); print('saved t11')
