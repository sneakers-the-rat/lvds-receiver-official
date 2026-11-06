import pcbnew
SRC='scratch/work/t_v5.kicad_pcb'; OUT='scratch/work/t_v6.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
code=b.GetNetcodeFromNetname('GND')
v=pcbnew.PCB_VIA(b); v.SetNetCode(code)
v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(88.3),pcbnew.FromMM(8.6)))
v.SetWidth(pcbnew.FromMM(0.6)); v.SetDrill(pcbnew.FromMM(0.3))
v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
