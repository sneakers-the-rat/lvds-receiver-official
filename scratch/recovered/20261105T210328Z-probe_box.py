import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
T = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])
x0, x1, y0, y1 = [float(a) for a in sys.argv[2:6]]
LN = {0: 'F', 2: 'In1', 4: 'In2', 31: 'B'}
def inb(x, y): return x0 <= x <= x1 and y0 <= y <= y1
for fp in board.GetFootprints():
    for p in fp.Pads():
        x, y = T(p.GetPosition().x), T(p.GetPosition().y)
        if inb(x, y):
            ls = [LN.get(l, str(l)) for l in (0, 2, 4, 31) if p.IsOnLayer(l)]
            print(f'PAD {fp.GetReference()}.{p.GetNumber()} {p.GetNetname()} ({x:.2f},{y:.2f}) {T(p.GetSize().x):.2f}x{T(p.GetSize().y):.2f} L={ls}')
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        x, y = T(t.GetPosition().x), T(t.GetPosition().y)
        if inb(x, y):
            print(f'VIA {t.GetNetname()} ({x:.2f},{y:.2f}) d={T(t.GetWidth()):.2f}')
    else:
        sx, sy, ex, ey = T(t.GetStart().x), T(t.GetStart().y), T(t.GetEnd().x), T(t.GetEnd().y)
        if inb((sx+ex)/2, (sy+ey)/2) or inb(sx, sy) or inb(ex, ey):
            print(f'TRK {t.GetNetname()} L{LN.get(t.GetLayer(), t.GetLayer())} ({sx:.2f},{sy:.2f})->({ex:.2f},{ey:.2f}) w={T(t.GetWidth()):.2f}')
