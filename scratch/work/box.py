import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
X0,X1,Y0,Y1 = map(float, sys.argv[2:6])
def mm(v): return pcbnew.ToMM(v)
L = {0:'F',2:'In1',4:'In2',31:'B'}
for t in b.GetTracks():
    s, e = t.GetStart(), t.GetEnd()
    sp, ep = (mm(s.x),mm(s.y)), (mm(e.x),mm(e.y))
    if max(sp[0],ep[0])<X0 or min(sp[0],ep[0])>X1 or max(sp[1],ep[1])<Y0 or min(sp[1],ep[1])>Y1: continue
    ln = L.get(t.GetLayer(), str(t.GetLayer()))
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f'VIA {ln} {t.GetNetname()} at ({sp[0]:.3f},{sp[1]:.3f}) d={mm(t.GetDrillValue()):.2f}/{mm(t.GetWidth()):.2f}')
    else:
        print(f'TRK {ln} {t.GetNetname()} ({sp[0]:.3f},{sp[1]:.3f})->({ep[0]:.3f},{ep[1]:.3f}) w={mm(t.GetWidth()):.2f}')
print('--- pads')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        p = pad.GetPosition(); x,y = mm(p.x), mm(p.y)
        if X0<=x<=X1 and Y0<=y<=Y1:
            sz = pad.GetSize()
            print(f'PAD {fp.GetReference()}.{pad.GetNumber()} {pad.GetNetname()} ({x:.3f},{y:.3f}) {mm(sz.x):.2f}x{mm(sz.y):.2f}')
