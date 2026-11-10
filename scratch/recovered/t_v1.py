import pcbnew
SRC='hw/pdlvds_rx.exp207.kicad_pcb'; OUT='scratch/work/t_v1.kicad_pcb'
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
# ULPI_D3: F east -> via (79.7,13.9) -> In2 diagonal south of D4's ->
# via-in-pad (89.35,5.1) on U6.69
trk('ULPI_D3',(78.438,13.75),(79.2,13.75),0.2,'F')
trk('ULPI_D3',(79.2,13.75),(79.7,13.9),0.2,'F')
via('ULPI_D3',(79.7,13.9))
trk('ULPI_D3',(79.7,13.9),(83.5,9.9),0.25,'In2')
trk('ULPI_D3',(83.5,9.9),(88.9,4.5),0.25,'In2')
trk('ULPI_D3',(88.9,4.5),(89.35,5.1),0.25,'In2')
via('ULPI_D3',(89.35,5.1))
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
