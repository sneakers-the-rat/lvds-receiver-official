import sys, pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp184.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
tx, ty = float(sys.argv[1]), float(sys.argv[2])
LAYERS = [(pcbnew.In1_Cu,'In1'), (pcbnew.In2_Cu,'In2'), (pcbnew.B_Cu,'B')]
for lay, ln in LAYERS:
    print('---', ln)
    for t in b.GetTracks():
        if t.GetLayer() != lay and not (t.Type() == pcbnew.PCB_VIA_T and t.IsOnLayer(lay)): continue
        s, e = t.GetStart(), t.GetEnd()
        sp, ep = (mm(s.x),mm(s.y)), (mm(e.x),mm(e.y))
        if max(sp[0],ep[0]) < tx-2 or min(sp[0],ep[0]) > tx+2 or max(sp[1],ep[1]) < ty-2 or min(sp[1],ep[1]) > ty+2: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            print(f'  VIA {t.GetNetname()} ({sp[0]:.3f},{sp[1]:.3f}) r={mm(t.GetWidth())/2:.2f}')
        else:
            print(f'  TRK {t.GetNetname()} ({sp[0]:.3f},{sp[1]:.3f})->({ep[0]:.3f},{ep[1]:.3f}) w={mm(t.GetWidth()):.2f}')
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(lay): continue
            pos = p.GetPosition(); px, py = mm(pos.x), mm(pos.y)
            if abs(px-tx) > 2 or abs(py-ty) > 2: continue
            sz = p.GetSize()
            print(f'  PAD {fp.GetReference()}.{p.GetNumber()} {p.GetNetname()} ({px:.3f},{py:.3f}) {mm(sz.x):.2f}x{mm(sz.y):.2f}')
