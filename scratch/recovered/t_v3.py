import pcbnew
SRC='scratch/work/t_v1.kicad_pcb'; OUT='scratch/work/t_v3.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
CODES={nm: b.GetNetcodeFromNetname(nm) for nm in ('ULPI_D3','ULPI_D4')}
M=pcbnew.FromMM
def key(t):
    s,e=t.GetStart(),t.GetEnd()
    return (round(pcbnew.ToMM(s.x),3),round(pcbnew.ToMM(s.y),3),round(pcbnew.ToMM(e.x),3),round(pcbnew.ToMM(e.y),3))
RIP={('ULPI_D4',(88.375,6.125,88.625,5.875)),('ULPI_D4',(88.625,5.875,88.875,5.875)),
     ('ULPI_D4',(88.875,5.875,89.125,5.875)),('ULPI_D4',(89.125,5.875,89.75,5.662)),
     ('ULPI_D4',(89.75,5.662,89.75,4.662)),
     ('ULPI_D4',(87.125,7.375,87.375,7.125)),('ULPI_D4',(87.375,7.125,87.625,6.875)),
     ('ULPI_D4',(87.625,6.875,87.875,6.625)),('ULPI_D4',(87.875,6.625,88.125,6.375)),
     ('ULPI_D4',(88.125,6.375,88.375,6.125)),
     # D3's In2 tail east of (86.8,7.05) is replaced by a via at (88.15,5.9) approach:
     ('ULPI_D3',(86.8,7.05,88.15,5.35))}
n=0
for t in list(b.GetTracks()):
    if isinstance(t,pcbnew.PCB_VIA):
        if t.GetNetname()=='ULPI_D4':
            p=t.GetPosition()
            if (round(pcbnew.ToMM(p.x),3),round(pcbnew.ToMM(p.y),3))==(88.375,6.125):
                b.Remove(t); n+=1
        if t.GetNetname()=='ULPI_D3':
            p=t.GetPosition()
            if (round(pcbnew.ToMM(p.x),3),round(pcbnew.ToMM(p.y),3))==(88.15,5.35):
                b.Remove(t); n+=1
        continue
    nm=t.GetNetname(); k=key(t)
    if (nm,k) in RIP or (nm,(k[2],k[3],k[0],k[1])) in RIP:
        b.Remove(t); n+=1
print("ripped",n)
V=lambda x,y: pcbnew.VECTOR2I(M(x),M(y))
def trk(nm,a,bb,w=0.25,lay=pcbnew.In2_Cu):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(CODES[nm])
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w)); t.SetLayer(lay); b.Add(t)
def via(nm,p,d=0.6):
    v=pcbnew.PCB_VIA(b); v.SetNetCode(CODES[nm])
    v.SetPosition(V(*p)); v.SetWidth(M(d)); v.SetDrill(M(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
# D4: new via on its own In2 diagonal at (86.9,7.6)
via('ULPI_D4',(86.9,7.6))
# D3: extend In2 from (86.8,7.05) to a via at (88.15,5.9)
trk('ULPI_D3',(86.8,7.05),(88.15,5.9))
via('ULPI_D3',(88.15,5.9))
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
