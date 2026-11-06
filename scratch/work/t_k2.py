import pcbnew
SRC='hw/pdlvds_rx.exp203.kicad_pcb'; OUT='scratch/work/t_k2.kicad_pcb'
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
# SDA head
trk('I2C_SDA',F,68.688,37.0,70.0,36.2,0.2)
trk('I2C_SDA',F,70.0,36.2,70.55,35.15,0.2)
via('I2C_SDA',70.55,35.15)
# In2 jog + south column x70.3
trk('I2C_SDA',I2,70.55,35.15,70.3,34.2)
trk('I2C_SDA',I2,70.3,34.2,70.3,27.6)
via('I2C_SDA',70.3,27.6)              # XO band hop
trk('I2C_SDA',B,70.3,27.6,70.3,25.4)
via('I2C_SDA',70.3,25.4)
trk('I2C_SDA',I2,70.3,25.4,70.3,23.3)
via('I2C_SDA',70.3,23.3)              # DM_PHY band hop
trk('I2C_SDA',B,70.3,23.3,70.3,21.5)
via('I2C_SDA',70.3,21.5)
trk('I2C_SDA',I2,70.3,21.5,70.3,10.8)
via('I2C_SDA',70.3,10.8)              # BIST band hop
trk('I2C_SDA',B,70.3,10.8,70.3,9.0)
via('I2C_SDA',70.3,9.0)
trk('I2C_SDA',I2,70.3,9.0,71.25,3.9)  # join In2 seg (71.125,4.125)-(71.375,3.625) mid-seg
# U9.6 via-in-pad
via('I2C_SDA',69.225,2.1,0.45,0.25)
trk('I2C_SDA',I2,69.225,2.1,69.7,1.2)
trk('I2C_SDA',I2,69.7,1.2,69.875,0.625)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
