import sys, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
for t in b.GetTracks():
    if t.GetNetname() != '+5V':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition())
        print(f'VIA ({p[0]:.3f},{p[1]:.3f})')
    else:
        a = pcbnew.ToMM(t.GetStart()); c = pcbnew.ToMM(t.GetEnd())
        if 30.8 < a[0] < 33.2 and -6.0 < a[1] < -3.6:
            print(f'SEG L{t.GetLayer()} ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{pcbnew.ToMM(t.GetWidth()):.2f}')
