import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241.kicad_pcb')
LAY = {0: 'F', 2: 'In2', 31: 'B'}
for t in b.GetTracks():
    if t.GetNetname() != 'CAP_CLK':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition())
        if abs(p[0] - 70.2) < 1.2 and abs(p[1] - 1.8) < 1.2:
            print(f'  via ({p[0]:.3f},{p[1]:.3f}) d{pcbnew.ToMM(t.GetWidth()):.2f}', flush=True)
    else:
        a = pcbnew.ToMM(t.GetStart()); c = pcbnew.ToMM(t.GetEnd())
        for q in (a, c):
            if abs(q[0] - 70.2) < 0.6 and abs(q[1] - 1.8) < 0.6:
                print(f'  seg {LAY[t.GetLayer()]} ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f})', flush=True)
                break
