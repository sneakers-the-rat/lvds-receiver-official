import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('scratch/work/exp217cand.kicad_pcb')
LAY = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
print('--- XO all tracks ---')
for t in b.GetTracks():
    if t.GetNetname() != 'XO':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        print(f'  via ({p[0]:.3f},{p[1]:.3f}) d{MM(t.GetWidth()):.2f}')
    else:
        a, c = MM(t.GetStart()), MM(t.GetEnd())
        print(f'  {LAY[t.GetLayer()]} ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
print('--- SQUELCH In2 items x in [81.4,82.4] ---')
for t in b.GetTracks():
    if t.GetNetname() != 'CDR_SQUELCH' or isinstance(t, pcbnew.PCB_VIA):
        continue
    if t.GetLayer() != pcbnew.In2_Cu:
        continue
    a, c = MM(t.GetStart()), MM(t.GetEnd())
    if max(a[0], c[0]) >= 81.4 and min(a[0], c[0]) <= 82.4:
        print(f'  ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
print('--- U6 pads 34,35 (XO targets?) and X1 pads ---')
for fp in b.GetFootprints():
    if fp.GetReference() in ('U6', 'X1'):
        for pad in fp.Pads():
            if pad.GetNetname() in ('XO', 'XI'):
                p = MM(pad.GetPosition())
                print(f'  {fp.GetReference()}.{pad.GetNumber()} {pad.GetNetname()} ({p[0]:.3f},{p[1]:.3f})')
