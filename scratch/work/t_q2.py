import pcbnew
SRC='hw/pdlvds_rx.exp206.kicad_pcb'; OUT='scratch/work/t_q2.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def net(n): return b.GetNetcodeFromNetname(n)
def trk(n,lay,x1,y1,x2,y2,w=0.2):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(net(n)); t.SetLayer(lay)
    t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2)); t.SetWidth(pcbnew.FromMM(w)); b.Add(t)
def via(n,x,y,d=0.5,dr=0.3):
    v=pcbnew.PCB_VIA(b); v.SetNetCode(net(n)); v.SetPosition(V(x,y))
    v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(dr))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
F=pcbnew.F_Cu
# SLICEP: F stub from U4.6 west tip WNW to via window (62.7,38.45)
trk('SLICEP',F,63.372,38.0,63.0,38.26)
trk('SLICEP',F,63.0,38.26,62.7,38.45)
via('SLICEP',62.7,38.45)
# C13.1 corner via: disc overlaps pad NW corner
via('SLICEP',60.25,37.5)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
