import pcbnew
SRC='hw/pdlvds_rx.exp208.kicad_pcb'; OUT='scratch/work/t_x1.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
M=pcbnew.FromMM; MM=pcbnew.ToMM
V=lambda x,y: pcbnew.VECTOR2I(M(x),M(y))
# inspect joint at (60.875,38.875)
for t in b.GetTracks():
    p=t.GetPosition() if t.Type()==pcbnew.PCB_VIA_T else None
    if p and abs(MM(p.x)-60.875)<0.01 and abs(MM(p.y)-38.875)<0.01:
        print("VIA at joint:", t.GetNetname(), MM(t.GetWidth()))
NAMES=('SLICEP','SLICEN','+3V3D_CDR','CDR_PIN','GND')
CODES={nm: b.GetNetcodeFromNetname(nm) for nm in NAMES}
print("netcodes:", CODES)
def trk(nm,a,bb,w=0.2,lay=pcbnew.F_Cu):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(CODES[nm])
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w)); t.SetLayer(lay); b.Add(t)
# --- move C51 west to (58.75,39.25); rip its +3V3D_CDR F feed segs ---
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
# --- re-lay C51.1 feed from the staircase joint (60.875,38.875) to new pad1 (57.8,39.25) ---
feed=[(60.875,38.875),(60.45,38.3),(58.55,38.15),(57.85,38.5),(57.8,39.25)]
for a,bb in zip(feed,feed[1:]): trk('+3V3D_CDR',a,bb)
# --- SLICEP: U4.6 (63.812,38.0) -> C13.1 new (58.225,41.75) ---
sp=[(63.812,38.0),(63.0,38.55),(61.0,38.7),(60.55,38.85),(60.55,40.3),(59.2,40.75),(58.8,41.4),(58.225,41.75)]
for a,bb in zip(sp,sp[1:]): trk('SLICEP',a,bb)
# --- SLICEN: U4.7 (63.812,38.5) -> C13.2 new (59.775,41.75) ---
sn=[(63.812,38.5),(63.3,38.75),(61.3,39.3),(61.05,39.45),(61.05,40.9),(60.4,41.35),(59.775,41.75)]
for a,bb in zip(sn,sn[1:]): trk('SLICEN',a,bb)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
# reload-verify netnames (save-rename law)
b2=pcbnew.LoadBoard(OUT)
import collections
c=collections.Counter()
for t in b2.GetTracks():
    if t.GetNetname() in ('SLICEP','SLICEN','+3V3D_CDR'): c[t.GetNetname()]+=1
print("reload track counts:",dict(c))
for fp in b2.GetFootprints():
    if fp.GetReference() in ('C51','C13'):
        p=fp.GetPosition(); print(fp.GetReference(),"at",round(MM(p.x),3),round(MM(p.y),3))
