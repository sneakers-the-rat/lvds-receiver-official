import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp187.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
for t in b.GetTracks():
    if t.GetNetname() != '+VA': continue
    s, e = t.GetStart(), t.GetEnd()
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f'VIA +VA ({mm(s.x):.3f},{mm(s.y):.3f})')
    else:
        print(f'TRK +VA {b.GetLayerName(t.GetLayer())} ({mm(s.x):.3f},{mm(s.y):.3f})->({mm(e.x):.3f},{mm(e.y):.3f}) w={mm(t.GetWidth()):.2f}')
