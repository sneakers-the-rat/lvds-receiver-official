import pcbnew
SRC='hw/pdlvds_rx.exp206.kicad_pcb'; OUT='scratch/work/t_r1.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
F=pcbnew.F_Cu; In2=pcbnew.In2_Cu
def net(name):
    ni=b.GetNetInfo(); return ni.GetNetItem(pcbnew.NETINFO_ITEM(name)) if False else b.FindNet(name)
def trk(netname, layer, w, x1,y1,x2,y2):
    t=pcbnew.PCB_TRACK(b); t.SetNet(net(netname)); t.SetLayer(layer)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1),pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2),pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(w)); b.Add(t); return t
def via(netname, x, y, d=0.5, drill=0.3):
    v=pcbnew.PCB_VIA(b); v.SetNet(net(netname))
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v); return v
# +3V3A needle: U7.25 pad north tip -> U7.16 pad (same net), x77.72 channel
trk('+3V3A', F, 0.15, 77.72,11.90, 77.72,16.20)
# XO: F stub + via + In2 underpass west then north into XO vertical x73.125
trk('XO', F, 0.20, 76.75,11.562, 76.75,10.70)
via('XO', 76.75,10.70)
trk('XO', In2, 0.25, 76.75,10.70, 76.75,9.65)
trk('XO', In2, 0.25, 76.75,9.65, 73.125,9.65)
trk('XO', In2, 0.25, 73.125,9.65, 73.125,11.375)
zf=pcbnew.ZONE_FILLER(b); zf.Fill(b.Zones())
b.Save(OUT); print('saved', OUT)
