import pcbnew
SRC='hw/pdlvds_rx.exp208.kicad_pcb'; OUT='scratch/work/t_x2.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
M=pcbnew.FromMM; MM=pcbnew.ToMM
V=lambda x,y: pcbnew.VECTOR2I(M(x),M(y))
NAMES=('SLICEP','SLICEN','+3V3D_CDR')
CODES={nm: b.GetNetcodeFromNetname(nm) for nm in NAMES}
def trk(nm,a,bb,w=0.2,lay=pcbnew.F_Cu):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(CODES[nm])
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w)); t.SetLayer(lay); b.Add(t)
def via(nm,p,d=0.5):
    v=pcbnew.PCB_VIA(b); v.SetNetCode(CODES[nm])
    v.SetPosition(V(*p)); v.SetWidth(M(d)); v.SetDrill(M(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
fps={fp.GetReference():fp for fp in b.GetFootprints()}
rip=[]
for t in list(b.GetTracks()):
    if t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetNetname()!='+3V3D_CDR' or t.GetLayer()!=pcbnew.F_Cu: continue
    s,e=t.GetStart(),t.GetEnd()
    pts={(round(MM(s.x),3),round(MM(s.y),3)),(round(MM(e.x),3),round(MM(e.y),3))}
    if pts=={(60.875,38.875),(60.55,39.25)} or pts=={(60.55,39.25),(60.3,39.25)}:
        rip.append(t)
for t in rip: b.Remove(t)
print("ripped feed segs:", len(rip))
fps['C51'].SetPosition(V(58.75,39.25))
fps['C13'].SetPosition(V(59.0,41.75))
# feed v2: south from the staircase via (60.875,38.875), west at y40.35, north into pad1 (57.8,39.25)
feed=[(60.875,38.875),(60.875,40.35),(57.9,40.35),(57.8,39.25)]
for a,bb in zip(feed,feed[1:]): trk('+3V3D_CDR',a,bb)
# SLICEP v2: west, jog south at x61.65 (clear of d0.8 via disc), approach C13.1 from east
sp=[(63.812,38.0),(63.3,38.0),(62.9,38.45),(61.65,38.6),(61.65,39.9),(61.3,40.85),(59.2,41.0),(58.8,41.4),(58.225,41.75)]
for a,bb in zip(sp,sp[1:]): trk('SLICEP',a,bb)
# SLICEN v2: F stub -> via (62.85,39.5) -> B west at y43.05 -> via (59.3,43.05) -> F tail into C13.2 south edge
snF=[(63.812,38.5),(63.15,38.6),(62.85,39.5)]
for a,bb in zip(snF,snF[1:]): trk('SLICEN',a,bb)
via('SLICEN',(62.85,39.5))
snB=[(62.85,39.5),(62.4,42.9),(62.0,43.05),(59.3,43.05)]
for a,bb in zip(snB,snB[1:]): trk('SLICEN',a,bb,lay=pcbnew.B_Cu)
via('SLICEN',(59.3,43.05))
snT=[(59.3,43.05),(59.775,42.55),(59.775,41.75)]
for a,bb in zip(snT,snT[1:]): trk('SLICEN',a,bb)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
b2=pcbnew.LoadBoard(OUT)
import collections
c=collections.Counter()
for t in b2.GetTracks():
    if t.GetNetname() in ('SLICEP','SLICEN','+3V3D_CDR'): c[t.GetNetname()]+=1
print("reload track counts:",dict(c))
