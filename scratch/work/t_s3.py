import pcbnew
SRC='scratch/work/gr_swclk_b.kicad_pcb'; OUT='scratch/work/t_s3.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
F=pcbnew.F_Cu
def trk(netname, layer, w, x1,y1,x2,y2):
    t=pcbnew.PCB_TRACK(b); t.SetNet(b.FindNet(netname)); t.SetLayer(layer)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1),pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2),pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(w)); b.Add(t); return t
v=pcbnew.PCB_VIA(b); v.SetNet(b.FindNet('SWCLK'))
v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(90.45),pcbnew.FromMM(-19.05)))
v.SetWidth(pcbnew.FromMM(0.5)); v.SetDrill(pcbnew.FromMM(0.3))
v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
trk('SWCLK', F, 0.20, 90.45,-19.05, 91.05,-18.90)
trk('SWCLK', F, 0.20, 91.05,-18.90, 91.00,-18.20)
trk('SWCLK', F, 0.20, 91.00,-18.20, 90.85,-17.30)
zf=pcbnew.ZONE_FILLER(b); zf.Fill(b.Zones())
b.Save(OUT); print('saved', OUT)
