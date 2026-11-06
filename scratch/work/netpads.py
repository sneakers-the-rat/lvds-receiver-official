import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[2] if len(sys.argv) > 2 else 'hw/pdlvds_rx.exp192.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
net = sys.argv[1]
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == net:
            pos = p.GetPosition(); sz = p.GetSize()
            print(f'{fp.GetReference()}.{p.GetNumber()} ({mm(pos.x):.3f},{mm(pos.y):.3f}) {mm(sz.x):.2f}x{mm(sz.y):.2f}')
for t in b.GetTracks():
    if t.GetNetname() != net: continue
    s, e = t.GetStart(), t.GetEnd()
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f'VIA ({mm(s.x):.3f},{mm(s.y):.3f})')
    else:
        print(f'TRK {b.GetLayerName(t.GetLayer())} ({mm(s.x):.3f},{mm(s.y):.3f})->({mm(e.x):.3f},{mm(e.y):.3f}) w={mm(t.GetWidth()):.2f}')
