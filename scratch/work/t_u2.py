import pcbnew
SRC='scratch/work/t_u1.kicad_pcb'; OUT='scratch/work/t_u2.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
MM=pcbnew.ToMM
def net(n): return b.GetNetcodeFromNetname(n)
def segkey(t):
    s,e=t.GetStart(),t.GetEnd()
    return tuple(sorted([(round(MM(s.x),3),round(MM(s.y),3)),
                         (round(MM(e.x),3),round(MM(e.y),3))]))
LAY={'F':pcbnew.F_Cu,'In2':pcbnew.In2_Cu,'B':pcbnew.B_Cu}
def trk(n,a,bb,w,lay):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(net(n))
    t.SetStart(V(*a)); t.SetEnd(V(*bb))
    t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(LAY[lay]); b.Add(t)
def via(n,p,d=0.6):
    v=pcbnew.PCB_VIA(b); v.SetNetCode(net(n))
    v.SetPosition(V(*p)); v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
# --- rip ALL ULPI_D1 copper except the pad stub (78.438,12.75)->(78.688,12.75)
keep={tuple(sorted(((78.438,12.75),(78.688,12.75))))}
ts=b.Tracks(); ALL=[ts[i] for i in range(ts.size())]
nrip=0
for t in ALL:
    if t.GetNetname()!='ULPI_D1': continue
    if t.Type()==pcbnew.PCB_VIA_T or segkey(t) not in keep:
        b.Remove(t); nrip+=1
print('D1 ripped items:', nrip)
# --- ULPI_D2: F east -> via (79.7,13.85) d0.5 -> In2 south -> via
# (80.05,7.0) -> B west -> via (78.6,6.2) -> F into U6.47 pad
trk('ULPI_D2',(78.438,13.25),(79.0,13.3),0.25,'F')
trk('ULPI_D2',(79.0,13.3),(79.7,13.85),0.25,'F')
via('ULPI_D2',(79.7,13.85),0.5)
trk('ULPI_D2',(79.7,13.85),(80.05,7.0),0.25,'In2')
via('ULPI_D2',(80.05,7.0))
trk('ULPI_D2',(80.05,7.0),(78.6,6.2),0.25,'B')
via('ULPI_D2',(78.6,6.2))
trk('ULPI_D2',(78.6,6.2),(78.3,5.6),0.2,'F')
trk('ULPI_D2',(78.3,5.6),(78.25,5.0),0.2,'F')
# --- ULPI_D1 re-fan: F south-east -> via (79.95,10.9) -> In2 east ->
# via (80.6,9.85) -> B west -> via (78.2,6.5) -> F stub into U6.46
trk('ULPI_D1',(78.688,12.75),(79.2,12.6),0.2,'F')
trk('ULPI_D1',(79.2,12.6),(79.3,11.5),0.2,'F')
trk('ULPI_D1',(79.3,11.5),(79.95,10.9),0.2,'F')
via('ULPI_D1',(79.95,10.9))
trk('ULPI_D1',(79.95,10.9),(80.6,9.85),0.25,'In2')
via('ULPI_D1',(80.6,9.85))
trk('ULPI_D1',(80.6,9.85),(78.2,6.5),0.25,'B')
via('ULPI_D1',(78.2,6.5))
trk('ULPI_D1',(78.2,6.5),(77.9,5.85),0.2,'F')
trk('ULPI_D1',(77.9,5.85),(77.75,5.662),0.2,'F')
trk('ULPI_D1',(77.75,5.662),(77.75,4.662),0.2,'F')
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
