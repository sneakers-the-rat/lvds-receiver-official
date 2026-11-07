import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp217.kicad_pcb')
LAY = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
print('--- pads in box x[68,76], y[11,18] (nets +3V3A/GND/PHY_1V8*) ---')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        p = MM(pad.GetPosition())
        if 68 <= p[0] <= 76 and 11 <= p[1] <= 18 and \
           pad.GetNetname() in ('+3V3A', 'GND', 'PHY_1V8', 'PHY_1V8A'):
            s = MM(pad.GetSize())
            print(f'  {fp.GetReference()}.{pad.GetNumber()} {pad.GetNetname()} ({p[0]:.3f},{p[1]:.3f}) size {s[0]:.2f}x{s[1]:.2f}')
print('--- tracks/vias in box, nets +3V3A/GND/PHY_1V8 ---')
for t in b.GetTracks():
    n = t.GetNetname()
    if n not in ('+3V3A', 'PHY_1V8'):
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if 66 <= p[0] <= 78 and 9 <= p[1] <= 20:
            print(f'  {n} via ({p[0]:.3f},{p[1]:.3f}) d{MM(t.GetWidth()):.2f}')
    else:
        a, c = MM(t.GetStart()), MM(t.GetEnd())
        if max(a[0], c[0]) >= 66 and min(a[0], c[0]) <= 78 and \
           max(a[1], c[1]) >= 9 and min(a[1], c[1]) <= 20:
            print(f'  {n} {LAY[t.GetLayer()]} ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
print('--- GND vias in box ---')
for t in b.GetTracks():
    if t.GetNetname() == 'GND' and isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if 66 <= p[0] <= 78 and 9 <= p[1] <= 20:
            print(f'  GND via ({p[0]:.3f},{p[1]:.3f}) d{MM(t.GetWidth()):.2f}')
