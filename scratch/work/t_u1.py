import pcbnew
SRC='hw/pdlvds_rx.exp206.kicad_pcb'; OUT='scratch/work/t_u1.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
MM=pcbnew.ToMM
def net(n): return b.GetNetcodeFromNetname(n)
def segkey(t):
    s,e=t.GetStart(),t.GetEnd()
    return tuple(sorted([(round(MM(s.x),3),round(MM(s.y),3)),
                         (round(MM(e.x),3),round(MM(e.y),3))]))
# rip +3V3D C48 feed chain: F remnant, F stub, old via, B w0.2 seg.
# KEEP B w0.6 seg (81.375,13.125)->(81.625,13.125): chain joint at
# 81.375 stays endpoint-to-endpoint with the new B seg below.
targets={tuple(sorted(t)) for t in [
    ((79.975,13.75),(79.975,13.5)),
    ((79.975,13.5),(80.125,13.125)),
    ((80.125,13.125),(81.375,13.125))]}
removed=[]
ts=b.Tracks(); ALL=[ts[i] for i in range(ts.size())]
for t in ALL:
    if t.GetNetname()!='+3V3D': continue
    if t.Type()==pcbnew.PCB_VIA_T:
        p=t.GetPosition()
        if abs(MM(p.x)-80.125)<0.01 and abs(MM(p.y)-13.125)<0.01:
            b.Remove(t); removed.append('via (80.125,13.125)')
    elif segkey(t) in targets:
        b.Remove(t); removed.append(f'seg {segkey(t)} L{t.GetLayer()}')
print('ripped:', removed)
# move C48 by (+0.85,-0.15): C48.1 -> (80.825,13.6), C48.2 -> (82.375,13.6)
for fp in b.GetFootprints():
    if fp.GetReference()=='C48':
        pos=fp.GetPosition()
        fp.SetPosition(V(MM(pos.x)+0.85, MM(pos.y)-0.15))
        for p in fp.Pads():
            pp=p.GetPosition()
            print('C48 pad', p.GetNumber(), p.GetNetname(),
                  round(MM(pp.x),3), round(MM(pp.y),3))
# new feed via at the SAME spot (80.35,13.125) d0.8/drill0.3 (v1 proved
# it electrically clean), B seg endpoint-to-endpoint to the kept joint
v=pcbnew.PCB_VIA(b); v.SetNetCode(net('+3V3D'))
v.SetPosition(V(80.35,13.125)); v.SetWidth(pcbnew.FromMM(0.8)); v.SetDrill(pcbnew.FromMM(0.3))
v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
t=pcbnew.PCB_TRACK(b); t.SetNetCode(net('+3V3D'))
t.SetStart(V(80.35,13.125)); t.SetEnd(V(81.375,13.125))
t.SetWidth(pcbnew.FromMM(0.6)); t.SetLayer(pcbnew.B_Cu); b.Add(t)
t=pcbnew.PCB_TRACK(b); t.SetNetCode(net('+3V3D'))
t.SetStart(V(80.825,13.6)); t.SetEnd(V(80.35,13.125))
t.SetWidth(pcbnew.FromMM(0.2)); t.SetLayer(pcbnew.F_Cu); b.Add(t)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
