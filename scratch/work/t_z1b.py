import pcbnew
MM=pcbnew.ToMM
for src in ('hw/pdlvds_rx.exp210.kicad_pcb','scratch/work/t_z1.kicad_pcb'):
    b=pcbnew.LoadBoard(src)
    hits=[]
    for t in b.GetTracks():
        s,e=t.GetStart(),t.GetEnd()
        if abs(MM(s.x)-70.0)<0.01 and abs(MM(s.y)-20.0)<0.01:
            hits.append((t.GetNetname(), b.GetLayerName(t.GetLayer()), MM(e.x), MM(e.y)))
    print(src, "tracks starting (70,20):", hits)
    n=sum(1 for t in b.GetTracks() if t.GetNetname()=='I2C_SDA' and b.GetLayerName(t.GetLayer())=='In1.Cu')
    print("  I2C_SDA In1 items:", n)
