import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MMt = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])
for ref in ('R29', 'R47', 'R34', 'R30', 'C32', 'D9'):
    fp = board.FindFootprintByReference(ref)
    if not fp: print(ref, 'NOT FOUND'); continue
    print(f"{ref} at ({MMt(fp.GetPosition().x):.2f},{MMt(fp.GetPosition().y):.2f}) rot={fp.GetOrientationDegrees()}")
    for p in fp.Pads():
        print(f"  {ref}.{p.GetNumber()} {p.GetNetname()} ({MMt(p.GetPosition().x):.3f},{MMt(p.GetPosition().y):.3f}) {MMt(p.GetSize().x):.2f}x{MMt(p.GetSize().y):.2f}")
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        x, y = MMt(t.GetPosition().x), MMt(t.GetPosition().y)
        if 42 <= x <= 50 and -10 <= y <= 4: print(f"  VIA {t.GetNetname()} @({x:.2f},{y:.2f})")
    else:
        sx, sy, ex, ey = MMt(t.GetStart().x), MMt(t.GetStart().y), MMt(t.GetEnd().x), MMt(t.GetEnd().y)
        cx, cy = (sx+ex)/2, (sy+ey)/2
        if 42 <= cx <= 50 and -10 <= cy <= 4:
            print(f"  TRK {t.GetNetname()} L{t.GetLayer()} ({sx:.2f},{sy:.2f})->({ex:.2f},{ey:.2f}) w={MMt(t.GetWidth()):.2f}")
