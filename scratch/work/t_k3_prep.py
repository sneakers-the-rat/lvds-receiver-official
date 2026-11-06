import pcbnew
b=pcbnew.LoadBoard('hw/pdlvds_rx.exp203.kicad_pcb')
V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
for fp in b.GetFootprints():
    if fp.GetReference()=='C14': fp.SetPosition(V(72.0,36.75))
b.Save('scratch/work/t_k3_base.kicad_pcb'); print("saved base")
