import pcbnew
b=pcbnew.LoadBoard('scratch/work/t_n2b.kicad_pcb')
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def net(n): return b.GetNetcodeFromNetname(n)
def trk(n,lay,x1,y1,x2,y2,w=0.25):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(net(n)); t.SetLayer(lay)
    t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2)); t.SetWidth(pcbnew.FromMM(w)); b.Add(t)
def via(n,x,y,d=0.5,dr=0.3):
    v=pcbnew.PCB_VIA(b); v.SetNetCode(net(n)); v.SetPosition(V(x,y))
    v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(dr))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
via('I2C_SDA',68.2,14.5)
trk('I2C_SDA',pcbnew.F_Cu,68.2,14.5,68.2,10.6)
via('I2C_SDA',68.2,10.6)
b.Save('scratch/work/t_n2c.kicad_pcb'); print("saved")
