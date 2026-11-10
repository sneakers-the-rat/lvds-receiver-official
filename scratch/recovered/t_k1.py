import pcbnew
SRC='hw/pdlvds_rx.exp203.kicad_pcb'; OUT='scratch/work/t_k1.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def net(n): return b.GetNetcodeFromNetname(n)[1]
def trk(n,lay,x1,y1,x2,y2,w=0.25):
    t=pcbnew.PCB_TRACK(b); t.SetNet(net(n)); t.SetLayer(lay)
    t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2)); t.SetWidth(pcbnew.FromMM(w)); b.Add(t)
def via(n,x,y,d=0.5,dr=0.3):
    v=pcbnew.PCB_VIA(b); v.SetNet(net(n)); v.SetPosition(V(x,y))
    v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(dr))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
F,I2,B=pcbnew.F_Cu,pcbnew.In2_Cu,pcbnew.B_Cu
# 1) C14 nudge +1.0 east
for fp in b.GetFootprints():
    if fp.GetReference()=='C14':
        fp.SetPosition(V(72.0,36.75))
# 2) SDA main: F exit + via + B dive + In2 corridor
trk('I2C_SDA',F,68.688,37.0,69.9,36.95,0.2)
via('I2C_SDA',69.9,36.95)
trk('I2C_SDA',B,69.9,36.95,68.9,32.5)
via('I2C_SDA',68.9,32.5)
trk('I2C_SDA',I2,68.9,32.5,69.3,28.3)
trk('I2C_SDA',I2,69.3,28.3,69.6,26.8)
trk('I2C_SDA',I2,69.6,26.8,74.9,26.3)
trk('I2C_SDA',I2,74.9,26.3,74.9,7.0)
trk('I2C_SDA',I2,74.9,7.0,73.375,7.625)
# 3) U9.6 hop
trk('I2C_SDA',F,69.45,2.1,70.05,2.35,0.2)
via('I2C_SDA',70.05,2.35)
trk('I2C_SDA',I2,70.05,2.35,70.875,1.625)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
