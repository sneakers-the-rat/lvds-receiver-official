import pcbnew
SRC='hw/pdlvds_rx.exp208.kicad_pcb'; OUT='scratch/work/t_x6.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
M=pcbnew.FromMM; MM=pcbnew.ToMM
V=lambda x,y: pcbnew.VECTOR2I(M(x),M(y))
NAMES=('SLICEP','SLICEN','+3V3D_CDR','GND','CDR_PIN')
CODES={nm: b.GetNetcodeFromNetname(nm) for nm in NAMES}
def trk(nm,a,bb,w=0.2,lay=pcbnew.F_Cu):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(CODES[nm])
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w)); t.SetLayer(lay); b.Add(t)
def via(nm,p,d=0.5,drill=0.3):
    v=pcbnew.PCB_VIA(b); v.SetNetCode(CODES[nm])
    v.SetPosition(V(*p)); v.SetWidth(M(d)); v.SetDrill(M(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
def segpts(t):
    s,e=t.GetStart(),t.GetEnd()
    return {(round(MM(s.x),3),round(MM(s.y),3)),(round(MM(e.x),3),round(MM(e.y),3))}
fps={fp.GetReference():fp for fp in b.GetFootprints()}
rip=[]
TARGETS=[{(60.875,38.875),(60.55,39.25)},{(60.55,39.25),(60.3,39.25)},
         {(63.562,37.5),(63.125,37.625)},{(63.125,37.625),(62.875,37.875)},{(62.875,37.875),(62.375,37.875)}]
for t in list(b.GetTracks()):
    if t.Type()==pcbnew.PCB_VIA_T: continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    if segpts(t) in TARGETS: rip.append(t)
for t in rip: b.Remove(t)
print("ripped segs:", len(rip))
# CDR_PIN jog re-lay: post moves west to (62.55,37.8), rejoins run at (62.375,37.875)
pn=[(63.562,37.5),(63.125,37.58),(62.55,37.8),(62.375,37.875)]
for a,bb in zip(pn,pn[1:]): trk('CDR_PIN',a,bb,w=0.2)
fps['C51'].SetPosition(V(58.75,39.25))
fps['C13'].SetPosition(V(59.0,41.75))
feed=[(60.875,38.875),(60.875,40.35),(57.9,40.35),(57.8,39.25)]
for a,bb in zip(feed,feed[1:]): trk('+3V3D_CDR',a,bb)
# SLICEP v5: shallow slope-0.3 diagonal, steep dive at x62.5, via (62.05,39.8), In2, tail
spF=[(63.812,38.0),(63.3,38.05),(62.6,38.26),(62.45,38.6),(61.65,38.75),(61.65,39.9),(62.05,39.8)]
for a,bb in zip(spF,spF[1:]): trk('SLICEP',a,bb)
via('SLICEP',(62.05,39.8))
spI=[(62.05,39.8),(60.9,41.0),(60.1,42.75),(59.9,43.55),(58.55,43.75)]
for a,bb in zip(spI,spI[1:]): trk('SLICEP',a,bb,lay=pcbnew.In2_Cu)
via('SLICEP',(58.55,43.75))
spT=[(58.55,43.75),(58.45,42.5),(58.225,41.75)]
for a,bb in zip(spT,spT[1:]): trk('SLICEP',a,bb)
# SLICEN v5: flat y38.575, vertical dive x63.0, via (63.0,39.35), B west, tail
snF=[(63.812,38.5),(63.0,38.575),(63.0,39.35)]
for a,bb in zip(snF,snF[1:]): trk('SLICEN',a,bb)
via('SLICEN',(63.0,39.35))
snB=[(63.0,39.35),(62.5,42.9),(62.0,43.05),(59.3,43.05)]
for a,bb in zip(snB,snB[1:]): trk('SLICEN',a,bb,lay=pcbnew.B_Cu)
via('SLICEN',(59.3,43.05))
snT=[(59.3,43.05),(59.775,42.55),(59.775,41.75)]
for a,bb in zip(snT,snT[1:]): trk('SLICEN',a,bb)
via('GND',(63.85,39.15),d=0.5)
via('GND',(59.0,38.9),d=0.5)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
b2=pcbnew.LoadBoard(OUT)
import collections
c=collections.Counter()
for t in b2.GetTracks():
    if t.GetNetname() in ('SLICEP','SLICEN','+3V3D_CDR','GND','CDR_PIN'): c[t.GetNetname()]+=1
print("reload track counts:",dict(c))
