import pcbnew
SRC='hw/pdlvds_rx.exp209.kicad_pcb'; OUT='scratch/work/t_y2.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
M=pcbnew.FromMM; MM=pcbnew.ToMM
V=lambda x,y: pcbnew.VECTOR2I(M(x),M(y))
CODE=b.GetNetcodeFromNetname('CDR_NIN')
def trk(a,bb,w=0.2,lay=pcbnew.F_Cu):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(CODE)
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w)); t.SetLayer(lay); b.Add(t)
def via(p,d=0.5):
    v=pcbnew.PCB_VIA(b); v.SetNetCode(CODE)
    v.SetPosition(V(*p)); v.SetWidth(M(d)); v.SetDrill(M(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
nF=[(63.812,37.0),(62.6,36.85),(61.75,36.7)]
for a,bb in zip(nF,nF[1:]): trk(a,bb)
via((61.75,36.7))
nI=[(61.75,36.7),(61.0,36.2),(60.3,37.0),(59.9,38.2),(59.95,39.4),(58.5,40.6),(56.0,42.3),(54.0,43.4),(51.45,45.5)]
for a,bb in zip(nI,nI[1:]): trk(a,bb,lay=pcbnew.In2_Cu)
via((51.45,45.5))
trk((51.45,45.5),(50.775,45.5))
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
b2=pcbnew.LoadBoard(OUT)
n=sum(1 for t in b2.GetTracks() if t.GetNetname()=='CDR_NIN')
print("reload CDR_NIN items:",n)
