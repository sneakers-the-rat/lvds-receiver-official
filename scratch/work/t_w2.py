import pcbnew
SRC='hw/pdlvds_rx.exp208.kicad_pcb'; OUT='scratch/work/t_w2.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
CODES={nm: b.GetNetcodeFromNetname(nm) for nm in ('ULPI_DIR','ULPI_NXT','ULPI_STP')}
M=pcbnew.FromMM
V=lambda x,y: pcbnew.VECTOR2I(M(x),M(y))
def trk(nm,a,bb,w=0.2,lay=pcbnew.F_Cu):
    t=pcbnew.PCB_TRACK(b); t.SetNetCode(CODES[nm])
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w)); t.SetLayer(lay); b.Add(t)
def via(nm,p,d=0.6):
    v=pcbnew.PCB_VIA(b); v.SetNetCode(CODES[nm])
    v.SetPosition(V(*p)); v.SetWidth(M(d)); v.SetDrill(M(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
# U7 south-face escapes v2 (C20.1/C22.1/C28.1/U5.1 avoided)
trk('ULPI_NXT',(75.25,16.438),(75.1,17.1)); trk('ULPI_NXT',(75.1,17.1),(74.4,17.75)); trk('ULPI_NXT',(74.4,17.75),(73.9,18.2)); via('ULPI_NXT',(73.9,18.2))
trk('ULPI_DIR',(75.75,16.438),(75.75,17.4)); trk('ULPI_DIR',(75.75,17.4),(74.7,18.1)); trk('ULPI_DIR',(74.7,18.1),(73.7,19.5)); via('ULPI_DIR',(73.7,19.5))
trk('ULPI_STP',(76.25,16.438),(76.25,17.6)); trk('ULPI_STP',(76.25,17.6),(76.45,19.3)); trk('ULPI_STP',(76.45,19.3),(76.3,20.9)); trk('ULPI_STP',(76.3,20.9),(73.9,21.2)); via('ULPI_STP',(73.9,21.2))
# U6 west-face stubs (F, from the west)
trk('ULPI_STP',(70.2,-2.25),(71.338,-2.25)); via('ULPI_STP',(70.2,-2.25))
trk('ULPI_DIR',(70.2,-1.25),(71.338,-1.25)); via('ULPI_DIR',(70.2,-1.25))
trk('ULPI_NXT',(70.2,-0.75),(71.338,-0.75)); via('ULPI_NXT',(70.2,-0.75))
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
