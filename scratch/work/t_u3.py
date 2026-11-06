import pcbnew
SRC='scratch/work/t_u2b.kicad_pcb'; OUT='scratch/work/t_u3.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def net(n): return b.GetNetcodeFromNetname(n)
LAY={'F':pcbnew.F_Cu,'In2':pcbnew.In2_Cu,'B':pcbnew.B_Cu}
def trk(n,a,bb,w,lay):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(net(n))
    t.SetStart(V(*a)); t.SetEnd(V(*bb))
    t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(LAY[lay]); b.Add(t)
def via(n,p,d=0.6):
    v=pcbnew.PCB_VIA(b); v.SetNetCode(net(n))
    v.SetPosition(V(*p)); v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
# ULPI_D1 v3: F west of U7 EP -> via (77.85,10.95) -> In2 south ->
# via (77.6,7.0) -> F stub into U6.46
trk('ULPI_D1',(78.688,12.75),(77.9,12.45),0.2,'F')
trk('ULPI_D1',(77.9,12.45),(77.85,10.95),0.2,'F')
via('ULPI_D1',(77.85,10.95))
trk('ULPI_D1',(77.85,10.95),(77.35,8.6),0.25,'In2')
trk('ULPI_D1',(77.35,8.6),(77.6,7.0),0.25,'In2')
via('ULPI_D1',(77.6,7.0))
trk('ULPI_D1',(77.6,7.0),(77.75,5.662),0.2,'F')
trk('ULPI_D1',(77.75,5.662),(77.75,4.662),0.2,'F')
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
