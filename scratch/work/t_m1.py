import pcbnew
SRC='hw/pdlvds_rx.exp203.kicad_pcb'; OUT='scratch/work/t_m1.kicad_pcb'
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
# +3V3D_CDR U4.12: F north stub, via, In2 drop to staircase vertex (66.625,38.375)
trk('+3V3D_CDR',F,66.0,39.688,66.0,40.15,0.2)
trk('+3V3D_CDR',F,66.0,40.15,66.45,40.3,0.2)
via('+3V3D_CDR',66.45,40.3)
trk('+3V3D_CDR',I2,66.45,40.3,66.45,38.55)
trk('+3V3D_CDR',I2,66.45,38.55,66.625,38.375)
# REFCLKN: F stub, via, B east at y41, dive, via, F into C14.1 (new pos 71.225,36.75)
trk('REFCLKN',F,65.5,39.688,65.5,40.1,0.2)
trk('REFCLKN',F,65.5,40.1,65.6,40.35,0.2)
via('REFCLKN',65.6,40.35)
trk('REFCLKN',B,65.6,40.35,65.6,41.0)
trk('REFCLKN',B,65.6,41.0,70.75,41.0)
trk('REFCLKN',B,70.75,41.0,71.7,37.55)
via('REFCLKN',71.7,37.55)
trk('REFCLKN',F,71.7,37.55,71.225,36.95,0.2)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
