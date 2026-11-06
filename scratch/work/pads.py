import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[5] if len(sys.argv) > 5 else 'hw/pdlvds_rx.exp196.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
X0,X1,Y0,Y1 = (float(v) for v in sys.argv[1:5])
for fp in b.GetFootprints():
    for p in fp.Pads():
        pos = p.GetPosition(); px, py = mm(pos.x), mm(pos.y)
        if X0 <= px <= X1 and Y0 <= py <= Y1:
            sz = p.GetSize()
            print(f'{fp.GetReference()}.{p.GetNumber()} {p.GetNetname()} ({px:.3f},{py:.3f}) {mm(sz.x):.2f}x{mm(sz.y):.2f}')
