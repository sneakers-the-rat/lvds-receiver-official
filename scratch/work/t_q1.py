import pcbnew
SRC='hw/pdlvds_rx.exp205.kicad_pcb'; OUT='scratch/work/t_q1.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def net(n): return b.GetNetcodeFromNetname(n)
# via-in-pad d0.5/drill0.3 on U9.6, centre shifted NE to (69.32,2.14):
# clears SCL via (69.375,1.375) d0.6 by 0.217 and U9.5 +3V3A pad by 0.21
v=pcbnew.PCB_VIA(b); v.SetNetCode(net('I2C_SDA'))
v.SetPosition(V(69.32,2.14)); v.SetWidth(pcbnew.FromMM(0.5)); v.SetDrill(pcbnew.FromMM(0.3))
v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved",OUT)
