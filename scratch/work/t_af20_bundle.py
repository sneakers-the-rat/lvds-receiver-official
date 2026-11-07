import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('scratch/work/exp217cand.kicad_pcb')
LAY = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
for t in b.GetTracks():
    n = t.GetNetname()
    if not (n.startswith('ULPI_D') or n in ('I2C_SDA','I2C_SCL','+3V3D')):
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if p[0] > 80.5:
            print(f'{n} via ({p[0]:.3f},{p[1]:.3f}) d{MM(t.GetWidth()):.2f}')
    else:
        a, c = MM(t.GetStart()), MM(t.GetEnd())
        if max(a[0], c[0]) > 80.5 and min(a[1], c[1]) < 17:
            print(f'{n} {LAY[t.GetLayer()]} ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
# U6 pads 69..76
for fp in b.GetFootprints():
    if fp.GetReference() == 'U6':
        for pad in fp.Pads():
            if pad.GetNumber() in ('69','70','71','72','73','74','75','76'):
                p = MM(pad.GetPosition())
                print(f'U6.{pad.GetNumber()} {pad.GetNetname()} at ({p[0]:.3f},{p[1]:.3f})')
