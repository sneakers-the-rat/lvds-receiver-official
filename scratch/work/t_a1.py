import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp198.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
net = b.FindNet('+3V3A')
# via on the NE corner of U7.25's pad (annulus overlaps the pad)
v = pcbnew.PCB_VIA(b)
v.SetPosition(pcbnew.VECTOR2I(M(77.86), M(11.35)))
v.SetDrill(M(0.3)); v.SetWidth(M(0.5))
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNet(net); b.Add(v)
# In2 run south then diagonal into the fat +3V3A vertical x=77.38 (w0.6)
pts = [(77.86,11.35), (77.86,12.6), (77.45,13.35)]
for a, bb in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
    t.SetWidth(M(0.3)); t.SetLayer(pcbnew.In2_Cu); t.SetNet(net); b.Add(t)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_a1.kicad_pcb'); print('saved t_a1')
