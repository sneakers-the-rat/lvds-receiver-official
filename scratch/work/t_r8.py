import pcbnew
SRC='hw/pdlvds_rx.exp206.kicad_pcb'; OUT='scratch/work/t_r8.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
F=pcbnew.F_Cu; In2=pcbnew.In2_Cu; Bc=pcbnew.B_Cu
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
# U7.6 +3V3A: no rips. F stub W then SW to via E of the GND stitch via,
# In2 W at y15.15 (S of DP/+3V3D via discs), N at x67.5, B hop into spine.
trk('+3V3A', F, 0.20, 73.122,14.75, 72.95,14.70)
trk('+3V3A', F, 0.20, 72.95,14.70, 72.85,14.50)
via('+3V3A', 72.78,14.42)
trk('+3V3A', In2, 0.25, 72.78,14.42, 72.60,15.15)
trk('+3V3A', In2, 0.25, 72.60,15.15, 67.50,15.15)
trk('+3V3A', In2, 0.25, 67.50,15.15, 67.50,15.65)
via('+3V3A', 67.50,15.65)
trk('+3V3A', Bc, 0.25, 67.50,15.65, 68.625,15.65)
zf=pcbnew.ZONE_FILLER(b); zf.Fill(b.Zones())
b.Save(OUT); print('saved', OUT)
