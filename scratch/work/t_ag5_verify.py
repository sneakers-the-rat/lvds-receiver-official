"""t_ag5: reload-verify a trial board: netname census for the
touched nets (save-rename check) + group census for XO/D5."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
from collections import Counter
c = Counter()
for t in b.GetTracks():
    c[t.GetNetname()] += 1
for n in ('XO', 'ULPI_D5', 'ULPI_D4', 'ULPI_D6', 'XI', 'I2C_SCL',
          'CDR_SQUELCH', 'GND'):
    print(f'{n}: {c[n]} tracks/vias')
print('--- XO items near old/new lane ---')
for t in b.GetTracks():
    if t.GetNetname() != 'XO':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if p[0] > 84:
            print(f'  via ({p[0]:.3f},{p[1]:.3f}) d{MM(t.GetWidth()):.2f}')
    else:
        a, cc = MM(t.GetStart()), MM(t.GetEnd())
        if a[0] > 80 and a[1] < 18 and t.GetLayer() == pcbnew.In2_Cu:
            print(f'  In2 ({a[0]:.3f},{a[1]:.3f})->({cc[0]:.3f},'
                  f'{cc[1]:.3f}) w{MM(t.GetWidth()):.2f}')
print('--- ULPI_D5 items ---')
for t in b.GetTracks():
    if t.GetNetname() != 'ULPI_D5':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        print(f'  via ({p[0]:.3f},{p[1]:.3f}) d{MM(t.GetWidth()):.2f}')
    else:
        a, cc = MM(t.GetStart()), MM(t.GetEnd())
        lay = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2',
               pcbnew.B_Cu: 'B'}[t.GetLayer()]
        print(f'  {lay} ({a[0]:.3f},{a[1]:.3f})->({cc[0]:.3f},'
              f'{cc[1]:.3f}) w{MM(t.GetWidth()):.2f}')
