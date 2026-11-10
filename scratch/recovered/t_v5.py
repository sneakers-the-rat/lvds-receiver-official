import pcbnew
SRC='scratch/work/t_v3h.kicad_pcb'; OUT='scratch/work/t_v5.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
CODES={nm: b.GetNetcodeFromNetname(nm) for nm in ('ULPI_D3','ULPI_D4','VCAP2')}
M=pcbnew.FromMM
def key(t):
    s,e=t.GetStart(),t.GetEnd()
    return (round(pcbnew.ToMM(s.x),3),round(pcbnew.ToMM(s.y),3),round(pcbnew.ToMM(e.x),3),round(pcbnew.ToMM(e.y),3))
RIP={('ULPI_D4',(87.375,7.125,87.625,6.875)),('ULPI_D4',(87.625,6.875,87.875,6.625)),
     ('ULPI_D4',(87.875,6.625,88.375,6.625)),('ULPI_D4',(88.375,6.625,88.625,6.375)),
     ('ULPI_D4',(88.625,6.375,88.875,6.125)),('ULPI_D4',(88.875,6.125,89.125,5.875)),
     ('ULPI_D4',(89.125,5.875,89.375,5.875)),('ULPI_D4',(89.375,5.875,89.625,5.625)),
     ('ULPI_D4',(89.625,5.625,89.75,5.412)),('ULPI_D4',(89.75,5.412,89.75,4.662)),
     ('VCAP2',(89.225,7.0,89.625,6.375)),('VCAP2',(89.625,6.375,90.25,6.162))}
n=0
for t in list(b.GetTracks()):
    if isinstance(t,pcbnew.PCB_VIA): continue
    nm=t.GetNetname(); k=key(t)
    if (nm,k) in RIP or (nm,(k[2],k[3],k[0],k[1])) in RIP:
        b.Remove(t); n+=1
print("ripped",n)
V=lambda x,y: pcbnew.VECTOR2I(M(x),M(y))
def trk(nm,a,bb,w=0.2):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(CODES[nm])
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w)); t.SetLayer(pcbnew.F_Cu); b.Add(t)
trk('VCAP2',(89.225,7.0),(89.9,6.9))
trk('VCAP2',(89.9,6.9),(90.25,6.162))
trk('ULPI_D4',(87.35,7.15),(88.6,6.6))
trk('ULPI_D4',(88.6,6.6),(89.55,6.62))
trk('ULPI_D4',(89.55,6.62),(89.75,5.662))
trk('ULPI_D4',(89.75,5.662),(89.75,4.662))
trk('ULPI_D3',(88.15,5.9),(88.5,6.15))
trk('ULPI_D3',(88.5,6.15),(89.25,6.15))
trk('ULPI_D3',(89.25,6.15),(89.25,5.662))
trk('ULPI_D3',(89.25,5.662),(89.25,4.662))
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
