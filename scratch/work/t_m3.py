import pcbnew
SRC='hw/pdlvds_rx.exp203.kicad_pcb'; OUT='scratch/work/t_m3.kicad_pcb'
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
for fp in b.GetFootprints():
    if fp.GetReference()=='C14': fp.SetPosition(V(72.0,36.75))
# REFCLKN: F north, channel east at y40.44, north through C15 gap, via (66.5,41.35), B east, dive, F into C14.1
trk('REFCLKN',F,65.5,39.688,65.5,40.44,0.2)
trk('REFCLKN',F,65.5,40.44,66.5,40.44,0.2)
trk('REFCLKN',F,66.5,40.44,66.5,41.35,0.2)
via('REFCLKN',66.5,41.35)
trk('REFCLKN',B,66.5,41.35,70.75,41.0)
trk('REFCLKN',B,70.75,41.0,71.7,37.55)
via('REFCLKN',71.7,37.55)
trk('REFCLKN',F,71.7,37.55,71.225,36.95,0.2)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
