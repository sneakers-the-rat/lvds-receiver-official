import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1 else 'hw/pdlvds_rx.exp188.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
X0,X1,Y0,Y1 = (float(v) for v in sys.argv[2:6])
for t in b.GetTracks():
    if t.Type() != pcbnew.PCB_VIA_T: continue
    p = t.GetPosition(); px, py = mm(p.x), mm(p.y)
    if X0 <= px <= X1 and Y0 <= py <= Y1:
        print(f'VIA {t.GetNetname()} ({px:.3f},{py:.3f}) d={mm(t.GetDrill()):.2f}/{mm(t.GetWidth()):.2f}')
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH: continue
        pos = p.GetPosition(); px, py = mm(pos.x), mm(pos.y)
        if X0 <= px <= X1 and Y0 <= py <= Y1:
            print(f'PTH {fp.GetReference()}.{p.GetNumber()} {p.GetNetname()} ({px:.3f},{py:.3f})')
