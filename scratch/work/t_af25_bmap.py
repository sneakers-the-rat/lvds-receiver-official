import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp217.kicad_pcb')
print('--- B items, x[78.5,95], y[0,16.5] ---')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if 78.5 <= p[0] <= 95 and 0 <= p[1] <= 16.5:
            print(f'  {t.GetNetname()} via ({p[0]:.3f},{p[1]:.3f}) d{MM(t.GetWidth()):.2f}')
    elif t.GetLayer() == pcbnew.B_Cu:
        a, c = MM(t.GetStart()), MM(t.GetEnd())
        if max(a[0], c[0]) >= 78.5 and min(a[0], c[0]) <= 95 and \
           max(a[1], c[1]) >= 0 and min(a[1], c[1]) <= 16.5:
            print(f'  {t.GetNetname()} B ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
