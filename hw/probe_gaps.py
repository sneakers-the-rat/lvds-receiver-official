import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MMt = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])
print('--- TP_HV tracks y in [11,23] ---')
for t in board.GetTracks():
    if t.GetNetname() != 'TP_HV' or t.Type() == pcbnew.PCB_VIA_T:
        continue
    sy, ey = MMt(t.GetStart().y), MMt(t.GetEnd().y)
    if 11 <= (sy + ey) / 2 <= 23:
        print(f'TRK L{t.GetLayer()} ({MMt(t.GetStart().x):.2f},{sy:.2f})->({MMt(t.GetEnd().x):.2f},{ey:.2f})')
print('--- APD_K vias x[33,44] y[-7,2] ---')
for t in board.GetTracks():
    if t.Type() != pcbnew.PCB_VIA_T:
        continue
    x, y = MMt(t.GetPosition().x), MMt(t.GetPosition().y)
    if 33 <= x <= 44 and -7 <= y <= 2:
        print(f'VIA {t.GetNetname()} @({x:.2f},{y:.2f}) d={MMt(t.GetWidth()):.2f}')
print('--- ALL items near CC2 seg (30.5,72.55)-(30.9,72.3) ---')
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        x, y = MMt(t.GetPosition().x), MMt(t.GetPosition().y)
        if 29.3 <= x <= 31.8 and 71.4 <= y <= 73.6:
            print(f'VIA {t.GetNetname()} @({x:.2f},{y:.2f}) d={MMt(t.GetWidth()):.2f}')
    else:
        sx, sy, ex, ey = MMt(t.GetStart().x), MMt(t.GetStart().y), MMt(t.GetEnd().x), MMt(t.GetEnd().y)
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        if 29.3 <= mx <= 31.8 and 71.4 <= my <= 73.6:
            print(f'TRK {t.GetNetname()} L{t.GetLayer()} ({sx:.2f},{sy:.2f})->({ex:.2f},{ey:.2f}) w={MMt(t.GetWidth()):.2f}')
print('--- GND tracks near U14.6 stub x[59.8,61.3] y[62.8,65.2] ---')
for t in board.GetTracks():
    if t.GetNetname() != 'GND' or t.Type() == pcbnew.PCB_VIA_T:
        continue
    sx, sy, ex, ey = MMt(t.GetStart().x), MMt(t.GetStart().y), MMt(t.GetEnd().x), MMt(t.GetEnd().y)
    if min(sx, ex) <= 61.3 and max(sx, ex) >= 59.8 and min(sy, ey) <= 65.2 and max(sy, ey) >= 62.8:
        print(f'TRK GND L{t.GetLayer()} ({sx:.2f},{sy:.2f})->({ex:.2f},{ey:.2f}) w={MMt(t.GetWidth()):.2f}')
