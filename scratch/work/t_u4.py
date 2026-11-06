import pcbnew
SRC='scratch/work/t_u1.kicad_pcb'; OUT='scratch/work/t_u4.kicad_pcb'
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
# rip D1 except pad stub
keep={tuple(sorted(((78.438,12.75),(78.688,12.75))))}
ts=b.Tracks(); ALL=[ts[i] for i in range(ts.size())]
n=0
for t in ALL:
    if t.GetNetname()!='ULPI_D1': continue
    if t.Type()==pcbnew.PCB_VIA_T or segkey(t) not in keep:
        b.Remove(t); n+=1
print('D1 ripped:', n)
# JOINT F-only plan, two channels out of the pocket mouth.
# D1 west channel x79.02 -> jog east of D0 bulge -> x79.35 -> tail
D1=[((78.688,12.75),(79.18,12.6)),((79.18,12.6),(79.18,11.0)),
    ((79.18,11.0),(79.35,10.35)),((79.35,10.35),(79.35,7.55)),
    ((79.35,7.55),(78.8,7.15)),((78.8,7.15),(78.2,6.6)),
    ((78.2,6.6),(77.85,6.1)),((77.85,6.1),(77.75,5.662)),
    ((77.75,5.662),(77.75,4.662))]
for a,bb in D1: trk('ULPI_D1',a,bb,0.2,'F')
# D2 east channel x79.45 -> jog east under C19.1 -> x79.8 -> tail
D2=[((78.438,13.25),(78.688,13.25)),((78.688,13.25),(79.125,13.125)),
    ((79.125,13.125),(79.45,12.95)),((79.45,12.95),(79.45,11.5)),
    ((79.45,11.5),(79.8,10.5)),((79.8,10.5),(79.8,7.6)),
    ((79.8,7.6),(79.3,6.6)),((79.3,6.6),(78.7,6.0)),
    ((78.7,6.0),(78.3,5.5)),((78.3,5.5),(78.25,5.0))]
for a,bb in D2: trk('ULPI_D2',a,bb,0.2,'F')
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
