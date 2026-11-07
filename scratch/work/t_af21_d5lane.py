import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('scratch/work/exp217cand.kicad_pcb')
LAY = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
print('--- D6 journey east of x=82.3 ---')
for t in b.GetTracks():
    if t.GetNetname() != 'ULPI_D6':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if p[0] > 82.3:
            print(f'  via ({p[0]:.3f},{p[1]:.3f}) d{MM(t.GetWidth()):.2f}')
    else:
        a, c = MM(t.GetStart()), MM(t.GetEnd())
        if max(a[0], c[0]) > 82.3:
            print(f'  {LAY[t.GetLayer()]} ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
print('--- arrival box x[89,97] y[0,6], all nets ---')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if 89 <= p[0] <= 97 and 0 <= p[1] <= 6:
            print(f'  {t.GetNetname()} via ({p[0]:.3f},{p[1]:.3f}) d{MM(t.GetWidth()):.2f}')
    else:
        a, c = MM(t.GetStart()), MM(t.GetEnd())
        if max(a[0], c[0]) >= 89 and min(a[0], c[0]) <= 97 and \
           max(a[1], c[1]) >= 0 and min(a[1], c[1]) <= 6:
            print(f'  {t.GetNetname()} {LAY[t.GetLayer()]} ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
print('--- In2 items with x+y in [95.9,97.2], x in [82,94] ---')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() != pcbnew.In2_Cu:
        continue
    a, c = MM(t.GetStart()), MM(t.GetEnd())
    for (x, y) in (a, c):
        if 82 <= x <= 94 and 95.9 <= x + y <= 97.2:
            print(f'  {t.GetNetname()} In2 ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
            break
