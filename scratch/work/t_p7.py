import pcbnew
SRC='hw/pdlvds_rx.exp204.kicad_pcb'; OUT='scratch/work/t_p7.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def net(n): return b.GetNetcodeFromNetname(n)
def trk(n,lay,x1,y1,x2,y2,w=0.25):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(net(n)); t.SetLayer(lay)
    t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2)); t.SetWidth(pcbnew.FromMM(w)); b.Add(t)
F=pcbnew.F_Cu
# rip GND U10.5 east fanout: seg (26.0,-2.0)-(26.57,-2.0) + via (26.58,-2.0)
ts=b.Tracks(); all_ts=[ts[i] for i in range(ts.size())]
def ep(t):
    s,e=t.GetStart(),t.GetEnd()
    return ((pcbnew.ToMM(s.x),pcbnew.ToMM(s.y)),(pcbnew.ToMM(e.x),pcbnew.ToMM(e.y)))
for t in all_ts:
    n=t.GetNetname()
    if n!='GND': continue
    (a,bb)=ep(t)
    if t.Type()==pcbnew.PCB_VIA_T and abs(a[0]-26.58)<0.01 and abs(a[1]+2.0)<0.01: b.Remove(t); print("ripped GND via")
    if t.Type()!=pcbnew.PCB_VIA_T and abs(a[0]-26.0)<0.02 and abs(a[1]+2.0)<0.02 and abs(bb[0]-26.57)<0.02 and abs(bb[1]+2.0)<0.02: b.Remove(t); print("ripped GND seg")
# HV_SS east channel
trk("HV_SS",F,26.075,-3.0,26.37,-3.0,0.15)
trk('HV_SS',F,26.37,-3.0,26.37,-1.1,0.15)
trk("HV_SS",F,26.37,-1.1,27.475,-1.05,0.15)
trk('HV_SS',F,27.475,-1.05,27.475,-0.9,0.2)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
