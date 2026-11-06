import sys, pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp188.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
want = sys.argv[1]
for t in b.GetTracks():
    if b.GetLayerName(t.GetLayer()) != want: continue
    s, e = t.GetStart(), t.GetEnd()
    sp, ep = (mm(s.x),mm(s.y)), (mm(e.x),mm(e.y))
    if max(sp[0],ep[0]) < 35 or min(sp[0],ep[0]) > 40 or max(sp[1],ep[1]) < 34 or min(sp[1],ep[1]) > 41: continue
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f'VIA {t.GetNetname()} ({sp[0]:.3f},{sp[1]:.3f}) d={mm(t.GetDrill())}/{mm(t.GetWidth())}')
    else:
        print(f'TRK {t.GetNetname()} ({sp[0]:.3f},{sp[1]:.3f})->({ep[0]:.3f},{ep[1]:.3f}) w={mm(t.GetWidth()):.2f}')
