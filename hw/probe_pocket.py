import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MMt = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])
# box around R31.1 pocket + U14/U13/J1 pad dumps
for ref in ('U14', 'U13', 'J1', 'U7'):
    fp = board.FindFootprintByReference(ref)
    print(f'{ref} at ({MMt(fp.GetPosition().x):.2f},{MMt(fp.GetPosition().y):.2f})')
    for p in fp.Pads():
        print(f'  {ref}.{p.GetNumber()} {p.GetNetname()} ({MMt(p.GetPosition().x):.2f},{MMt(p.GetPosition().y):.2f}) {MMt(p.GetSize().x):.2f}x{MMt(p.GetSize().y):.2f}')
print('--- R31 pocket x[29,37] y[-4,4] ---')
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        x, y = MMt(t.GetPosition().x), MMt(t.GetPosition().y)
        if 29 <= x <= 37 and -4 <= y <= 4: print(f'  VIA {t.GetNetname()} @({x:.2f},{y:.2f}) d={MMt(t.GetWidth()):.2f}')
    else:
        sx, sy, ex, ey = MMt(t.GetStart().x), MMt(t.GetStart().y), MMt(t.GetEnd().x), MMt(t.GetEnd().y)
        cx, cy = (sx+ex)/2, (sy+ey)/2
        if 29 <= cx <= 37 and -4 <= cy <= 4:
            print(f'  TRK {t.GetNetname()} L{t.GetLayer()} ({sx:.2f},{sy:.2f})->({ex:.2f},{ey:.2f}) w={MMt(t.GetWidth()):.2f}')
