import pcbnew
SRC='hw/pdlvds_rx.exp210.kicad_pcb'; OUT='scratch/work/t_z1.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
M=pcbnew.FromMM
V=lambda x,y: pcbnew.VECTOR2I(M(x),M(y))
CODE=b.GetNetcodeFromNetname('I2C_SDA')
t=pcbnew.PCB_TRACK(b); t.SetNetCode(CODE)
t.SetStart(V(70.0,20.0)); t.SetEnd(V(70.0,25.0)); t.SetWidth(M(0.2)); t.SetLayer(pcbnew.In1_Cu); b.Add(t)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT)
b2=pcbnew.LoadBoard(OUT)
for t2 in b2.GetTracks():
    s,e=t2.GetStart(),t2.GetEnd()
    if abs(pcbnew.ToMM(s.x)-70.0)<0.01 and pcbnew.ToMM(s.y)>19.0 and pcbnew.ToMM(s.y)<26.0:
        print("reload netname:", t2.GetNetname(), "layer:", b2.GetLayerName(t2.GetLayer()))
print("zones In1:", [ (z.GetNetname(), z.GetLayer()) for z in b2.Zones() if b2.GetLayerName(z.GetLayer())=='In1.Cu'][:3])
