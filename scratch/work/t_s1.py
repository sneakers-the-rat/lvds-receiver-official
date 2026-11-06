import pcbnew
SRC='scratch/work/gr_swclk_b.kicad_pcb'; OUT='scratch/work/t_s1.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
v=pcbnew.PCB_VIA(b); v.SetNet(b.FindNet('SWCLK'))
v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(90.875),pcbnew.FromMM(-17.375)))
v.SetWidth(pcbnew.FromMM(0.5)); v.SetDrill(pcbnew.FromMM(0.3))
v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
zf=pcbnew.ZONE_FILLER(b); zf.Fill(b.Zones())
b.Save(OUT); print('saved', OUT)
