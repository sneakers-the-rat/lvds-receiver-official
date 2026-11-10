import sys, pcbnew
want = sys.argv[1]
X0, X1, Y0, Y1 = (float(v) for v in sys.argv[2:6])
board = sys.argv[6] if len(sys.argv) > 6 else 'hw/pdlvds_rx.exp189.kicad_pcb'
b = pcbnew.LoadBoard(board)
def mm(v): return pcbnew.ToMM(v)
for t in b.GetTracks():
    if b.GetLayerName(t.GetLayer()) != want: continue
    s, e = t.GetStart(), t.GetEnd()
    sp, ep = (mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))
    if max(sp[0], ep[0]) < X0 or min(sp[0], ep[0]) > X1 or max(sp[1], ep[1]) < Y0 or min(sp[1], ep[1]) > Y1: continue
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f'VIA {t.GetNetname()} ({sp[0]:.3f},{sp[1]:.3f}) d={mm(t.GetDrill())}/{mm(t.GetWidth())}')
    else:
        print(f'TRK {t.GetNetname()} ({sp[0]:.3f},{sp[1]:.3f})->({ep[0]:.3f},{ep[1]:.3f}) w={mm(t.GetWidth()):.2f}')
