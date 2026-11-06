import pcbnew
b=pcbnew.LoadBoard('hw/pdlvds_rx.exp204.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def net(n): return b.GetNetcodeFromNetname(n)
def trk(n,lay,x1,y1,x2,y2,w=0.25):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(net(n)); t.SetLayer(lay)
    t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2)); t.SetWidth(pcbnew.FromMM(w)); b.Add(t)
ts=b.Tracks(); ALL=[ts[i] for i in range(ts.size())]
def rip(n,x1,y1,x2,y2):
    for t in ALL:
        if t.GetNetname()!=n or t.Type()==pcbnew.PCB_VIA_T: continue
        s,e=t.GetStart(),t.GetEnd()
        pts={(round(mm(s.x),3),round(mm(s.y),3)),(round(mm(e.x),3),round(mm(e.y),3))}
        if pts=={(x1,y1),(x2,y2)}: b.Remove(t); return True
    print("RIP MISS",n,x1,y1,x2,y2); return False
I2=pcbnew.In2_Cu
# XO In2 vertical relay: x69.625 -> x69.35
rip('XO',69.625,31.625,69.625,27.125)
trk('XO',I2,69.625,31.625,69.35,31.35)
trk('XO',I2,69.35,31.35,69.35,27.3)
trk('XO',I2,69.35,27.3,69.625,27.125)
b.Save('scratch/work/t_n1_base.kicad_pcb'); print("saved")
