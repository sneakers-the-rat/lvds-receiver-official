import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp217.kicad_pcb')
LAY = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if 75.5 <= p[0] <= 80.5 and 8.5 <= p[1] <= 14.5:
            print(f'  {t.GetNetname()} via ({p[0]:.3f},{p[1]:.3f}) d{MM(t.GetWidth()):.2f}')
    else:
        a, c = MM(t.GetStart()), MM(t.GetEnd())
        if max(a[0], c[0]) >= 75.5 and min(a[0], c[0]) <= 80.5 and \
           max(a[1], c[1]) >= 8.5 and min(a[1], c[1]) <= 14.5:
            print(f'  {t.GetNetname()} {LAY[t.GetLayer()]} ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        p = MM(pad.GetPosition())
        if 75.5 <= p[0] <= 80.5 and 8.5 <= p[1] <= 14.5:
            print(f'  PAD {fp.GetReference()}.{pad.GetNumber()} {pad.GetNetname()} ({p[0]:.3f},{p[1]:.3f})')
