import pcbnew
SRC='hw/pdlvds_rx.exp206.kicad_pcb'; OUT='scratch/work/t_r3.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
F=pcbnew.F_Cu; In2=pcbnew.In2_Cu
def net(name): return b.FindNet(name)
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
# XO plan B: F drop + west run under the south row (dip S around +3V3A stub end
# (74.625,10.875)), via W of ULPI_CK In2 vertical, In2 hop into XO's own path.
trk('XO', F, 0.20, 76.75,11.562, 76.75,10.80)
trk('XO', F, 0.20, 76.75,10.80, 75.40,10.80)
trk('XO', F, 0.20, 75.40,10.80, 75.05,10.45)
trk('XO', F, 0.20, 75.05,10.45, 74.30,10.45)
trk('XO', F, 0.20, 74.30,10.45, 74.00,10.80)
via('XO', 74.00,10.80)
trk('XO', In2, 0.25, 74.00,10.80, 72.95,10.80)
zf=pcbnew.ZONE_FILLER(b); zf.Fill(b.Zones())
b.Save(OUT); print('saved', OUT)
