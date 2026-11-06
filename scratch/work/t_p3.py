import pcbnew
SRC='hw/pdlvds_rx.exp204.kicad_pcb'; OUT='scratch/work/t_p3.kicad_pcb'
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
# HV_SS: F east, north in x26.4 channel, east into C30.1 south edge
trk('HV_SS',F,26.075,-3.0,26.4,-3.0,0.2)
trk('HV_SS',F,26.4,-3.0,26.4,-1.6,0.2)
trk('HV_SS',F,26.4,-1.6,27.475,-1.2,0.2)
trk('HV_SS',F,27.475,-1.2,27.475,-0.9,0.2)
# HV_INTVCC: F needle, via, In2 north under GATE B web, via, F into C31.1
trk('HV_INTVCC',F,30.375,-3.0,30.9,-3.05,0.2)
via('HV_INTVCC',31.05,-3.05)
trk('HV_INTVCC',I2,31.05,-3.05,31.1,-1.1)
via('HV_INTVCC',31.1,-1.1)
trk('HV_INTVCC',F,31.1,-1.1,31.225,-0.9,0.2)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
