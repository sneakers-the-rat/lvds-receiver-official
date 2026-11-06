import pcbnew
SRC='hw/pdlvds_rx.exp203.kicad_pcb'; OUT='scratch/work/t_m5.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def mm(v): return pcbnew.ToMM(v)
def net(n): return b.GetNetcodeFromNetname(n)
def trk(n,lay,x1,y1,x2,y2,w=0.25):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(net(n)); t.SetLayer(lay)
    t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2)); t.SetWidth(pcbnew.FromMM(w)); b.Add(t)
def via(n,x,y,d=0.5,dr=0.3):
    v=pcbnew.PCB_VIA(b); v.SetNetCode(net(n)); v.SetPosition(V(x,y))
    v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(dr))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
F,I2,B=pcbnew.F_Cu,pcbnew.In2_Cu,pcbnew.B_Cu
# collect tracks once (Remove degrades wrappers)
ts=b.Tracks(); ALL=[ts[i] for i in range(ts.size())]
def rip(n,x1,y1,x2,y2):
    for t in ALL:
        if t.GetNetname()!=n or t.Type()==pcbnew.PCB_VIA_T: continue
        s,e=t.GetStart(),t.GetEnd()
        pts={(round(mm(s.x),3),round(mm(s.y),3)),(round(mm(e.x),3),round(mm(e.y),3))}
        if pts=={(x1,y1),(x2,y2)}: b.Remove(t); return True
    print("RIP MISS",n,x1,y1,x2,y2); return False
for fp in b.GetFootprints():
    if fp.GetReference()=='C14': fp.SetPosition(V(72.0,36.75))
    if fp.GetReference()=='C15': fp.SetPosition(V(66.5,42.3))
# CF1 re-land: rip west line + drop, new north detour into moved C15.1 (65.725,42.3)
rip('CF1',68.6,42.05,66.0,42.05); rip('CF1',66.0,42.05,66.0,41.55)
trk('CF1',F,68.6,40.52,68.6,43.1,0.2)
trk('CF1',F,68.6,43.1,66.0,43.1,0.2)
trk('CF1',F,66.0,43.1,66.0,42.5,0.2)
# CF2 re-land: rip pad stub, extend north into moved C15.2 (67.275,42.3)
rip('CF2',67.275,41.25,67.275,41.0)
trk('CF2',F,67.275,41.0,67.275,41.9,0.2)
# +3V3D_CDR U4.12: stub + via (66.0,40.45) + In2 drop to staircase vertex
trk('+3V3D_CDR',F,66.0,39.688,66.0,40.45,0.2)
via('+3V3D_CDR',66.0,40.45)
trk('+3V3D_CDR',I2,66.0,40.45,66.45,38.55)
trk('+3V3D_CDR',I2,66.45,38.55,66.625,38.375)
# REFCLKN: channel, arc over +3V3D via, gap via (66.5,41.35), B east, dive, F into C14.1
trk('REFCLKN',F,65.5,39.688,65.5,40.44,0.2)
trk('REFCLKN',F,65.5,40.44,65.75,41.0,0.2)
trk('REFCLKN',F,65.75,41.0,66.3,41.2,0.2)
trk('REFCLKN',F,66.3,41.2,66.5,41.35,0.2)
via('REFCLKN',66.5,41.35)
trk('REFCLKN',B,66.5,41.35,70.75,41.0)
trk('REFCLKN',B,70.75,41.0,71.7,37.55)
via('REFCLKN',71.7,37.55)
trk('REFCLKN',F,71.7,37.55,71.225,36.95,0.2)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
