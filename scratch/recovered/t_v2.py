import pcbnew
SRC='scratch/work/t_v1.kicad_pcb'; OUT='scratch/work/t_v2.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
M=pcbnew.FromMM
def key(t):
    s,e=t.GetStart(),t.GetEnd()
    return (round(pcbnew.ToMM(s.x),3),round(pcbnew.ToMM(s.y),3),round(pcbnew.ToMM(e.x),3),round(pcbnew.ToMM(e.y),3))
RIP={('ULPI_D4',(88.375,6.125,88.625,5.875)),('ULPI_D4',(88.625,5.875,88.875,5.875)),
     ('ULPI_D4',(88.875,5.875,89.125,5.875)),('ULPI_D4',(89.125,5.875,89.75,5.662))}
n=0
for t in list(b.GetTracks()):
    if isinstance(t,pcbnew.PCB_VIA): continue
    nm=t.GetNetname()
    if (nm,key(t)) in RIP or (nm,(key(t)[2],key(t)[3],key(t)[0],key(t)[1])) in RIP:
        b.Remove(t); n+=1
print("ripped",n)
V=lambda x,y: pcbnew.VECTOR2I(M(x),M(y))
def net(nm): return b.GetNetcodeFromNetname(nm)
def trk(nm,a,bb,w=0.2,lay=pcbnew.F_Cu):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(net(nm))
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w)); t.SetLayer(lay); b.Add(t)
# D4 new tail: east approach into pad70
trk('ULPI_D4',(88.375,6.125),(89.2,6.3))
trk('ULPI_D4',(89.2,6.3),(89.9,6.0))
trk('ULPI_D4',(89.9,6.0),(89.72,5.3))
trk('ULPI_D4',(89.72,5.3),(89.75,4.662))
# D3 tail in the vacated fan
trk('ULPI_D3',(88.15,5.35),(88.7,5.8))
trk('ULPI_D3',(88.7,5.8),(89.25,5.662))
trk('ULPI_D3',(89.25,5.662),(89.25,4.662))
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
