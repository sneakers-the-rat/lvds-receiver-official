import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MMt = pcbnew.ToMM
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp46.kicad_pcb')
n = 0
for t in board.GetTracks():
    if t.GetNetname() != 'TP_HV':
        continue
    n += 1
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f'VIA @({MMt(t.GetPosition().x):.2f},{MMt(t.GetPosition().y):.2f})')
    else:
        print(f'TRK L{t.GetLayer()} ({MMt(t.GetStart().x):.2f},{MMt(t.GetStart().y):.2f})->({MMt(t.GetEnd().x):.2f},{MMt(t.GetEnd().y):.2f}) w={MMt(t.GetWidth()):.2f}')
print('TP_HV tracks:', n)
