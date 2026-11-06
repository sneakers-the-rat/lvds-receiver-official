import pcbnew
SRC='hw/pdlvds_rx.exp204.kicad_pcb'; OUT='scratch/work/t_p5.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def net(n): return b.GetNetcodeFromNetname(n)
def trk(n,lay,x1,y1,x2,y2,w=0.25):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(net(n)); t.SetLayer(lay)
    t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2)); t.SetWidth(pcbnew.FromMM(w)); b.Add(t)
def via(n,x,y,d=0.5,dr=0.3):
    v=pcbnew.PCB_VIA(b); v.SetNetCode(net(n)); v.SetPosition(V(x,y))
    v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(dr))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
F,I2,B=pcbnew.F_Cu,pcbnew.In2_Cu,pcbnew.B_Cu
trk('HV_SS',F,24.625,-3.0,23.9,-2.9,0.2)
trk('HV_SS',F,23.9,-2.9,23.45,-1.2,0.2)
via('HV_SS',23.45,-1.2)
trk('HV_SS',B,23.45,-1.2,26.3,-1.25)
trk('HV_SS',B,26.3,-1.25,27.475,-1.6)
via('HV_SS',27.475,-1.6)
trk('HV_SS',F,27.475,-1.6,27.475,-0.9,0.2)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
