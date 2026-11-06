import pcbnew
SRC='hw/pdlvds_rx.exp204.kicad_pcb'; OUT='scratch/work/t_n2.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
def mm(v): return pcbnew.ToMM(v)
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def net(n): return b.GetNetcodeFromNetname(n)
def trk(n,lay,x1,y1,x2,y2,w=0.25):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(net(n)); t.SetLayer(lay)
    t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2)); t.SetWidth(pcbnew.FromMM(w)); b.Add(t)
def via(n,x,y,d=0.5,dr=0.3):
    v=pcbnew.PCB_VIA(b); v.SetNetCode(net(n)); v.SetPosition(V(x,y))
    v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(dr))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
ts=b.Tracks(); ALL=[ts[i] for i in range(ts.size())]
def rip(n,x1,y1,x2,y2):
    for t in ALL:
        if t.GetNetname()!=n or t.Type()==pcbnew.PCB_VIA_T: continue
        s,e=t.GetStart(),t.GetEnd()
        pts={(round(mm(s.x),3),round(mm(s.y),3)),(round(mm(e.x),3),round(mm(e.y),3))}
        if pts=={(x1,y1),(x2,y2)}: b.Remove(t); return True
    print("RIP MISS seg",n,x1,y1,x2,y2); return False
def ripvia(n,x,y):
    for t in ALL:
        if t.GetNetname()!=n or t.Type()!=pcbnew.PCB_VIA_T: continue
        s=t.GetStart()
        if (round(mm(s.x),3),round(mm(s.y),3))==(x,y): b.Remove(t); return True
    print("RIP MISS via",n,x,y); return False
F,I2,B=pcbnew.F_Cu,pcbnew.In2_Cu,pcbnew.B_Cu
# --- XO relay: via (69.625,31.625)->(69.3,31.625); F seg re-start; In2 vertical -> x69.3
rip('XO',69.625,31.625,69.875,31.375)
rip('XO',69.625,31.625,69.625,27.125)
ripvia('XO',69.625,31.625)
via('XO',69.3,31.625,0.6,0.3)
trk('XO',F,69.3,31.625,69.875,31.375,0.25)
trk('XO',I2,69.3,31.625,69.3,27.3)
trk('XO',I2,69.3,27.3,69.625,27.125)
# --- SDA head
trk('I2C_SDA',F,68.688,37.0,69.9,36.55,0.2)
trk('I2C_SDA',F,69.9,36.55,70.3,36.1,0.2)
via('I2C_SDA',70.3,36.1)
# --- In2 south through pinch at x69.95
trk('I2C_SDA',I2,70.3,36.1,69.95,34.9)
trk('I2C_SDA',I2,69.95,34.9,69.95,27.6)
via('I2C_SDA',69.95,27.6)
trk('I2C_SDA',B,69.95,27.6,69.95,24.9)   # XO + REFCLK bands hop
via('I2C_SDA',69.95,24.9)
trk('I2C_SDA',I2,69.95,24.9,69.95,23.6)
via('I2C_SDA',69.95,23.6)
trk('I2C_SDA',B,69.95,23.6,69.95,21.9)   # DM_PHY band hop
via('I2C_SDA',69.95,21.9)
b.Save(OUT); print("saved",OUT)
