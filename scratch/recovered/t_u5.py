import pcbnew
SRC='hw/pdlvds_rx.exp206.kicad_pcb'; OUT='scratch/work/t_u5.kicad_pcb'
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
# --- Phase A': C48 east (+0.85,-0.15); rip old +3V3D feed chain;
# new feed: F stub threading between C19.1/C19.2 to via (81.625,10.9)
# on the B vertical trunk.
targets={tuple(sorted(t)) for t in [
    ((79.975,13.75),(79.975,13.5)),
    ((79.975,13.5),(80.125,13.125)),
    ((80.125,13.125),(81.375,13.125)),
    ((81.375,13.125),(81.625,13.125))]}
ts=b.Tracks(); ALL=[ts[i] for i in range(ts.size())]
for t in ALL:
    if t.GetNetname()!='+3V3D': continue
    if t.Type()==pcbnew.PCB_VIA_T:
        p=t.GetPosition()
        if abs(MM(p.x)-80.125)<0.01 and abs(MM(p.y)-13.125)<0.01:
            b.Remove(t)
    elif segkey(t) in targets:
        b.Remove(t)
for fp in b.GetFootprints():
    if fp.GetReference()=='C48':
        pos=fp.GetPosition()
        fp.SetPosition(V(MM(pos.x)+0.85, MM(pos.y)-0.15))
trk('+3V3D',(80.825,13.6),(81.0,12.6),0.2,'F')
trk('+3V3D',(81.0,12.6),(81.0,11.0),0.2,'F')
trk('+3V3D',(81.0,11.0),(81.625,10.9),0.2,'F')
via('+3V3D',(81.625,10.9),0.8)
# --- rip D1 except pad stub
keep={tuple(sorted(((78.438,12.75),(78.688,12.75))))}
ts=b.Tracks(); ALL=[ts[i] for i in range(ts.size())]
for t in ALL:
    if t.GetNetname()!='ULPI_D1': continue
    if t.Type()==pcbnew.PCB_VIA_T or segkey(t) not in keep:
        b.Remove(t)
# --- D1: F channel (west), two jogs around D0's bulge
D1=[((78.688,12.75),(79.18,12.6)),((79.18,12.6),(79.18,11.95)),
    ((79.18,11.95),(78.95,11.5)),((78.95,11.5),(78.95,10.9)),
    ((78.95,10.9),(79.35,10.35)),((79.35,10.35),(79.35,7.55)),
    ((79.35,7.55),(78.8,7.15)),((78.8,7.15),(78.2,6.6)),
    ((78.2,6.6),(77.85,6.1)),((77.85,6.1),(77.75,5.662)),
    ((77.75,5.662),(77.75,4.662))]
for a,bb in D1: trk('ULPI_D1',a,bb,0.2,'F')
# --- D2: F mouth -> via (79.87,12.97) d0.5 -> In2 south -> via
# (79.75,7.75) -> F tail into U6.47
trk('ULPI_D2',(78.438,13.25),(78.688,13.25),0.2,'F')
trk('ULPI_D2',(78.688,13.25),(79.125,13.125),0.2,'F')
trk('ULPI_D2',(79.125,13.125),(79.87,12.97),0.2,'F')
via('ULPI_D2',(79.87,12.97),0.5)
trk('ULPI_D2',(79.87,12.97),(79.9,7.75),0.25,'In2')
via('ULPI_D2',(79.9,7.75))
trk('ULPI_D2',(79.9,7.75),(79.0,6.8),0.2,'F')
trk('ULPI_D2',(79.0,6.8),(78.45,6.1),0.2,'F')
trk('ULPI_D2',(78.45,6.1),(78.3,5.5),0.2,'F')
trk('ULPI_D2',(78.3,5.5),(78.25,5.0),0.2,'F')
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
